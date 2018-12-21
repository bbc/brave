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
        logger_name = 'brave.%s.%s.%d' % (self.input_output_overlay_or_mixer(), args['type'], args['id'])
        logger_format = '%%(levelname)s:\033[32m[%s %d]\033[0m %%(message)s' % \
            (self.input_output_overlay_or_mixer(), args['id'])
        self.logger = brave.helpers.get_logger(logger_name, logger_format)
        self.elements = {}
        self.probes = {}

        # Merge in the arguments:
        for a in args:
            if a != 'props':
                setattr(self, a, args[a])

        # Handle the props of this input:
        self._set_default_props()
        if 'props' in args and args['props'] is not None:
            self._update_props(args['props'])

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
            'initial_state': {
                'type': 'str',
                'default': 'PLAYING',
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
        Accepts updates to this elements.
        Note: may be overridden.
        '''
        if 'state' in updates:
            success = self.set_state(updates['state'])
            if not success:
                return False

        if 'props' in updates:
            self._update_props(updates['props'])
            self.handle_updated_props()

        return True

    def get_state(self):
        if hasattr(self, 'pipeline'):
            return self.pipeline.get_state(0).state
        else:
            return Gst.State.NULL

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

    def summarise(self):
        s = {
            'state': self.get_state().value_nick.upper(),
            'has_audio': self.has_audio(),
            'has_video': self.has_video(),
            'uid': self.uid()
        }

        attributes_to_copy = ['id', 'type', 'error_message', 'props', 'current_num_peers']
        for a in attributes_to_copy:
            if hasattr(self, a):
                s[a] = getattr(self, a)

        return s

    def uid(self):
        return '%s%d' % (self.input_output_overlay_or_mixer(), self.id)

    def src_connections(self):
        return []

    def dest_connections(self):
        return []

    def delete(self):
        '''
        Delete this block.
        Ensures any connections to/from this block are also deleted.
        '''
        self.logger.debug('Being deleted')
        connections = self.src_connections() + self.dest_connections()

        def iterate_through_connections():
            if len(connections) == 0:
                self._delete_with_no_connections()
            else:
                connection = connections.pop()
                connection.delete(callback=iterate_through_connections)

        iterate_through_connections()

    def _delete_with_no_connections(self):
        if not self.pipeline.set_state(Gst.State.NULL):
            self.logger.warning('Unable to set private pipe to NULL before attempting to delete')

        def remove_element(element):
            self.pipeline.remove(element)

        iterator = self.pipeline.iterate_elements()
        iterator.foreach(remove_element)
        del self.pipeline
        self.collection.pop(self.id)
        self.session().items_recently_deleted.append({'id': self.id, 'type': self.input_output_overlay_or_mixer()})

    def set_state(self, state):
        '''
        Set the state to NULL/READY/PAUSED/PLAYING.
        Only works for inputs and outputs that have their own pipeline.
        '''
        if not hasattr(self, 'pipeline'):
            self.logger.warning('set_state() called but no pipeline')
            return False

        response = self.pipeline.set_state(state)
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

    def on_state_change(self, old_state, new_state):
        '''
        Called when the state of this pipeline has changed.
        '''
        if old_state == Gst.State.NULL and new_state != Gst.State.NULL and hasattr(self, 'error_message'):
            delattr(self, 'error_message')
        self.logger.debug('Pipeline state change from %s to %s' %
                          (old_state.value_nick.upper(), new_state.value_nick.upper()))

        starting = (new_state in [Gst.State.PLAYING, Gst.State.PAUSED] and
                    old_state not in [Gst.State.PLAYING, Gst.State.PAUSED])
        if hasattr(self, 'on_pipeline_start') and starting:
            self.on_pipeline_start()

        GObject.timeout_add(1, self.__consider_initial_state, new_state)
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
        if 'width' in self.props and 'height' in self.props:
            return self.props['width'], self.props['height']
        else:
            return None, None

    def _set_default_props(self):
        '''
        Called by the constructor to set up any default props.
        '''
        self.props = {}
        for key, details in self.permitted_props().items():
            if 'default' in details:
                self.props[key] = details['default']

    def _update_props(self, new_props):
        '''
        Given a dict of new props, updates self.props
        Once complete, call self.handle_updated_props()
        '''
        permitted = self.permitted_props()

        for key, value in new_props.items():

            # First, warn about any known props:
            if key not in permitted:
                raise brave.exceptions.InvalidConfiguration(
                    'Invalid prop provided to %s: "%s"' % (self.input_output_overlay_or_mixer(), key))

            # None (null in JSON) means it should be unset (or default if there is one)
            elif value is None:
                if key in self.props:
                    self.props.pop(key, None)
                    if key in self.permitted_props():
                        if 'default' in self.permitted_props()[key]:
                            self.props[key] = self.permitted_props()[key]['default']

            else:
                # Set the type (int/float/str) if necessary
                if 'type' in permitted[key]:
                    try:
                        if permitted[key]['type'] == 'int':
                            value = int(value)
                        elif permitted[key]['type'] == 'float':
                            value = float(value)
                        elif permitted[key]['type'] == 'str':
                            value = str(value)
                        elif permitted[key]['type'] == 'bool':
                            if type(value) is not bool:
                                self.logger.warning(f'Property not boolean: "{str(value)}"')
                        else:
                            self.logger.warning(f'Do not know of type "{permitted[key]["type"]}"')
                    except ValueError:
                        self.logger.warning(f'Updated property "{str(value)}" is not a valid {type}, ignoring')

                if 'permitted_values' in permitted[key]:
                    if value not in permitted[key]['permitted_values']:
                        self.logger.warning('%s not in [%s]' % (value, permitted[key]['permitted_values']))
                        continue

                self.props[key] = value

    def __consider_initial_state(self, new_state):
        '''
        If the user has requested an initial state for this element, this method sets it at the correct time.
        '''
        should_go_to_initial_state = new_state == Gst.State.READY and 'initial_state' in self.props and \
            (not hasattr(self, 'initial_state_initiated') or not self.initial_state_initiated)
        if should_go_to_initial_state:
            self.logger.debug('Now at READY state, time to set initial state of "%s"' % self.props['initial_state'])
            state_to_change_to = state_string_to_constant(self.props['initial_state'])
            if state_to_change_to:
                self.set_state(state_to_change_to)
            else:
                self.logger.warning('Unable to set to initial unknown state "%s"' % self.props['initial_state'])
            self.initial_state_initiated = True

        return False
