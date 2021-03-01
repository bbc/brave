import brave.helpers
from gi.repository import Gst, GLib, GObject
from brave.pipeline_messaging import setup_messaging
import brave.config as config
import brave.exceptions
from brave.helpers import state_string_to_constant


class InputOutputOverlay():
    '''
    An abstract superclass representing an input, output, overlay, and mixer.
    '''
    def __init__(self, **args):
        for field in ['id', 'type', 'collection']:
            setattr(self, field, args[field])
        self.logger = brave.helpers.get_logger(self.input_output_overlay_or_mixer() + str(args['id']))
        self.elements = {}
        self.probes = {}
        self.setup_complete = False

        # All blocks go to PLAYING unless the user requests otherwise:
        self._desired_state = Gst.State.PLAYING

        # Handle the props of this input:
        self._set_props(args, updating=False)
        self._set_default_props()

        self.check_item_can_be_created()

    def session(self):
        return self.collection.session

    def check_item_can_be_created(self):
        '''
        Allows subclasses to define rules on whether they are createable
        '''
        pass

    def create_pipeline_from_string(self, pipeline_string):
        try:
            self.logger.debug('Creating with pipeline: ' + pipeline_string)
            self.pipeline = Gst.parse_launch(pipeline_string)
            setup_messaging(pipe=self.pipeline, parent_object=self)
        except GLib.GError as e:
            self.error_message = str(e)
            self.logger.error('Failed to create pipeline [%s]: %s' % (pipeline_string, self.error_message))
            raise brave.exceptions.PipelineFailure(self.error_message)

    def permitted_props(self):
        '''
        The properties that the user can set for this input/output.
        Likely overridden, to extend the list.
        '''
        return {
            'id': {
                'type': 'int',
                'updatable': False
            },
            'state': {
                'type': 'str',
                'uppercase': True,
                'permitted_values': {
                    'PLAYING': 'Playing',
                    'PAUSED': 'Paused',
                    'READY': 'Ready',
                    'NULL': 'Null'
                }
            }
        }

    def update(self, updates):
        '''
        Accepts updates to this block.
        Note: may be overridden.
        '''
        self._set_props(updates, updating=True)
        self.handle_updated_props()

    def handle_updated_props(self):
        '''
        Called when the user has updated certain properties of this block.
        '''
        pass  # overwritten by some subclasses

    def print_state_summary(self):
        '''
        Prints the state of all elements to STDOUT.
        '''
        by_state = {}

        def get_state_of_each_element(element):
            state = element.get_state(0).state.value_nick.upper()
            if state not in by_state:
                by_state[state] = []
            by_state[state].append(element.name)

        if hasattr(self, 'pipeline'):
            state = self.pipeline.get_state(0).state.value_nick.upper()
            by_state[state] = ['pipeline']
            iterator = self.pipeline.iterate_elements()
            iterator.foreach(get_state_of_each_element)

        for state, elements in by_state.items():
            self.logger.debug(f'In {state} state: {", ".join(elements)}')

    def has_video(self):
        return config.enable_video()

    def has_audio(self):
        return config.enable_audio()

    def summarise(self, for_config_file=False):
        '''
        Get a summary of this object
        'for_config_file' property limits to what is put in a Brave config file.
        '''
        attributes_to_copy = ['type'] + list(self.permitted_props().keys())
        s = {}

        if for_config_file:
            if self.desired_state:
                s['state'] = self.desired_state.value_nick.upper()
            else:
                s['state'] = self.state.value_nick.upper()
        else:
            attributes_to_copy += ['error_message', 'current_num_peers', 'uid']
            s['has_audio'] = self.has_audio()
            s['has_video'] = self.has_video()

            if hasattr(self, 'pipeline'):
                s['state'] = self.state.value_nick.upper()

            if self.desired_state:
                s['desired_state'] = self.desired_state.value_nick.upper()

        for a in attributes_to_copy:
            if a is not 'state' and hasattr(self, a):
                s[a] = getattr(self, a)

        return s

    @property
    def uid(self):
        return '%s%d' % (self.input_output_overlay_or_mixer(), self.id)

    def source_connections(self):
        return []

    def dest_connections(self):
        return []

    def delete(self):
        '''
        Delete this block.
        Ensures any connections to/from this block are also deleted.
        Also ensures any overlays attached to this block are unattached
        '''
        self.logger.debug('Being deleted')
        self.session().overlays.remove_source(self)
        connections = self.source_connections() + self.dest_connections()

        def iterate_through_connections():
            if len(connections) == 0:
                self._delete_with_no_connections()
            else:
                connection = connections.pop()
                connection.delete(callback=iterate_through_connections)

        iterate_through_connections()

    def _delete_with_no_connections(self):
        if not self.set_pipeline_state(Gst.State.NULL):
            self.logger.warning('Unable to set private pipe to NULL before attempting to delete')

        if hasattr(self, 'pipeline'):
            def remove_element(element):
                self.pipeline.remove(element)

            iterator = self.pipeline.iterate_elements()
            iterator.foreach(remove_element)
            del self.pipeline
        self.collection.pop(self.id)
        self.session().report_deleted_item(self)

    def set_desired_state(self, state):
        '''
        Reports a user request to change the state to NULL/READY/PAUSED/PLAYING.
        '''
        self.desired_state = state
        return self.set_pipeline_state(state)

    def set_pipeline_state(self, state):
        '''
        Set the pipeline's state to NULL/READY/PAUSED/PLAYING.
        '''

        if not hasattr(self, 'pipeline'):
            self.logger.warning('set_pipeline_state() called but no pipeline')
            return False

        # For debugging hanging state changes
        # print('TEMP About to call pipeline.set_state... may hang...')
        # import traceback
        # traceback.print_stack()
        response = self.pipeline.set_state(state)
        # print('Finished calling pipeline.set_state')

        if response == Gst.StateChangeReturn.SUCCESS:
            self.logger.debug(f"Move to state {state.value_nick.upper()} complete")
            return True
        elif response == Gst.StateChangeReturn.ASYNC:
            self.logger.debug(f"Move to state {state.value_nick.upper()} is IN PROGRESS")
            return True
        elif response == Gst.StateChangeReturn.NO_PREROLL:
            self.logger.debug(f"Move to state {state.value_nick.upper()} has completed but no data yet")
            return True
        else:
            self.logger.warning(f'Unable to set pipeline to \'{str(state.value_nick.upper())}\' state: {str(response)}')
            return False

    def on_state_change(self, old_state, new_state, pending_state):
        '''
        Called when the state of this pipeline has changed.
        '''
        if new_state is Gst.State.NULL:
            # Likely means an error has occured, so remove user request to change state:
            self.desired_state = None

        if old_state is Gst.State.NULL and new_state is not Gst.State.NULL:
            if hasattr(self, 'error_message'):
                delattr(self, 'error_message')

        if self.desired_state == new_state:
            self.desired_state = None

        in_transition_to_another_state = pending_state is not Gst.State.VOID_PENDING
        if in_transition_to_another_state:
            self.logger.debug('Pipeline state change from %s to %s (pending %s)' %
                              (old_state.value_nick.upper(), new_state.value_nick.upper(),
                               pending_state.value_nick.upper()))
        else:
            self.logger.debug('Pipeline state change from %s to %s' %
                              (old_state.value_nick.upper(), new_state.value_nick.upper()))

            # If the user's requested another state, now it's time to move to it:
            # Doing it in a separate thread may not be necessary.
            GObject.timeout_add(1, self._consider_changing_state)

        starting = (new_state in [Gst.State.PLAYING, Gst.State.PAUSED] and
                    old_state not in [Gst.State.PLAYING, Gst.State.PAUSED])
        if hasattr(self, 'on_pipeline_start') and starting:
            self.on_pipeline_start()

        self.report_update_to_user()

    def report_update_to_user(self):
        '''
        Report that this input/output/mixer has changed,
        and the update should be sent to the user via websocket.
        '''
        self.session().items_recently_updated.append(self)

    def get_dimensions(self):
        '''
        Get the width and height of this block.
        '''
        if hasattr(self, 'width') and hasattr(self, 'height'):
            return self.width, self.height
        else:
            return None, None

    def _set_default_props(self):
        '''
        Called by the constructor to set up any default props.
        '''
        for key, details in self.permitted_props().items():
            if 'required' in details and details['required'] and not hasattr(self, key):
                raise brave.exceptions.InvalidConfiguration('"%s" property is required' % key)
            if 'default' in details and not hasattr(self, key):
                setattr(self, key, details['default'])

    def _set_props(self, new_props, updating):
        '''
        Given a dict of new props, updates self
        Once complete, call self.handle_updated_props()
        '''
        permitted = self.permitted_props()

        for key, value in new_props.items():

            # TODO reconsider 'collection' - better way?
            if key in ['type', 'collection']:
                continue

            # First, warn about any known props:
            if key not in permitted:
                raise brave.exceptions.InvalidConfiguration(
                    'Invalid prop provided to %s: "%s"' % (self.uid, key))

            prop_details = permitted[key]

            # Some properties cannot be updated once set
            if updating and 'updatable' in prop_details and not prop_details['updatable']:
                if hasattr(self, key) and getattr(self, key) != value:
                    raise brave.exceptions.InvalidConfiguration('Cannot update "%s" field' % key)

            # None (null in JSON) means it should be unset (or default if there is one)
            if value is None:
                if 'permitted_values' in prop_details and None not in prop_details['permitted_values']:
                    raise brave.exceptions.InvalidConfiguration('Cannot set "%s" property to null' % key)
                if 'required' in prop_details and not prop_details['required']:
                    raise brave.exceptions.InvalidConfiguration('"%s" is a required property, cannot be null' % key)
                if hasattr(self, key):
                    delattr(self, key)
                    if key in self.permitted_props():
                        if 'default' in self.permitted_props()[key]:
                            setattr(self, key, self.permitted_props()[key]['default'])

            else:
                # Set the type (int/float/str) if necessary
                if 'type' in prop_details:
                    try:
                        if prop_details['type'] == 'int':
                            value = int(value)
                        elif prop_details['type'] == 'float':
                            value = float(value)
                        elif prop_details['type'] == 'str':
                            value = str(value)
                            if 'uppercase' in prop_details and prop_details['uppercase']:
                                value = value.upper()
                        elif prop_details['type'] == 'bool':
                            if type(value) is not bool:
                                self.logger.warning(f'Property not boolean: "{str(value)}"')
                        else:
                            self.logger.warning(f'Do not know of type "{prop_details["type"]}"')
                    except ValueError:
                        self.logger.warning('Updated property "%s" is not of type "%s", ignoring'
                                            % (value, prop_details['type']))

                if 'permitted_values' in prop_details:
                    if value not in prop_details['permitted_values']:
                        self.logger.warning('%s not in [%s]' % (value, prop_details['permitted_values']))
                        continue

                if key == 'uri' and self.uid.startswith("input"):
                    setattr(self, key, value + "_" + str(new_props["id"]))
                else:
                    setattr(self, key, value)

    @property
    def state(self):
        return self.pipeline.get_state(0).state if hasattr(self, 'pipeline') else Gst.State.NULL

    @state.setter
    def state(self, new_state):
        '''
        Allows the state to be set. Can be either a string (e.g. 'READY') or the Gst constant.
        '''
        if new_state is None:
            self._desired_state = None
            return

        if new_state not in [Gst.State.PLAYING, Gst.State.PAUSED, Gst.State.READY, Gst.State.NULL]:
            converted_state = state_string_to_constant(new_state)
            if not converted_state:
                raise brave.exceptions.InvalidConfiguration('Invalid state "%s"' % new_state)
            else:
                new_state = converted_state

        self.desired_state = new_state

        if self.setup_complete:
            self._consider_changing_state()

    @state.deleter
    def state(self):
        pass

    @property
    def desired_state(self):
        return self._desired_state

    @desired_state.setter
    def desired_state(self, new_state):
        self._desired_state = new_state

    @desired_state.deleter
    def desired_state(self):
        self._desired_state = None

    def _consider_changing_state(self):
        '''
        Called when the block is first started, or the state changes, to decide
        if an additional change needs to be made.
        '''
        if not self.setup_complete or not self.desired_state:
            return

        if self.state == self.desired_state:
            return

        if self.state is Gst.State.NULL:
            # We go NULL -> READY as a default.
            # If the user wants to go further (i.e. PAUSED/PLAYING) then this method will be called again.
            self.set_pipeline_state(Gst.State.READY)
            return

        if not self.desired_state:
            return

        if self.desired_state is Gst.State.PLAYING:
            # Force a manual strip through the PAUSED state. This allows buffering to occur.
            if self.state is not Gst.State.PAUSED:
                self.set_pipeline_state(Gst.State.PAUSED)
                return
            # Some block types want to wait until their buffer is full before proceeding to PLAYING:
            if not self._can_move_to_playing_state():
                return

        self.set_pipeline_state(self.desired_state)

    def _can_move_to_playing_state(self):
        return True  # Overridden by some subclasses
