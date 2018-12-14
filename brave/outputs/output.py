from gi.repository import Gst
from brave.helpers import round_down, create_intersink_channel_name, block_pad, unblock_pad
import brave.exceptions
from brave.inputoutputoverlay import InputOutputOverlay


class Output(InputOutputOverlay):
    '''
    An abstract superclass representing an output.
    '''

    def __init__(self, **args):
        super().__init__(**args)

        self._queue_into_intersink = {} # TODO remove once we have connection

        self._set_src()
        self.create_elements()

        if self.has_video():
            self.pipeline.get_by_name('capsfilter')\
                .set_property('caps', Gst.Caps.from_string(self.create_caps_string()))
            self.intervideosrc = self.pipeline.get_by_name('intervideosrc')
            self.intervideosrc_src_pad = self.intervideosrc.get_static_pad('src')

        if self.has_audio():
            self.interaudiosrc = self.pipeline.get_by_name('interaudiosrc')
            self.interaudiosrc_src_pad = self.interaudiosrc.get_static_pad('src')

        # This stores the pads on the source's tee which are connected to this output:
        self.tee_src_pads = {}

        if self.src():
            if self.has_video() and self.src().has_video():
                self.create_intervideosink_and_connections()

            if self.has_audio() and self.src().has_audio():
                self.create_interaudiosink_and_connections()

            self._sync_elements_on_src_pipeline()

            # Link this to the source (input or mixer), assuming there is one
            self.link_from_source()

        # Set initially to READY, and when there we set to self.props['initial_state']
        self.set_state(Gst.State.READY)

    def input_output_overlay_or_mixer(self):
        return 'output'

    def permitted_props(self):
        return {
            **super().permitted_props(),
            'mixer_id': {
                'type': 'int'
            },
            'input_id': {
                'type': 'int'
            }
        }

    def src(self):
        '''
        Returns the Input or Mixer that is the source for this output.
        Can be None if this outpu thas no source.
        '''
        connection = self.src_connection()
        if connection:
            return connection.src
        else:
            return None

    def src_connection(self):
        '''
        Returns an the Connection object which describes what this output is connected to.
        If this output is not connected to anything, returns None.
        An output can be the destination to exactly one connection.
        The source of a connection will be either an Input or a Mixer.
        '''
        return self.session().connections.get_first_collection_for_dest(self)

    def src_connections(self):
        '''
        As src_connection() but returns an array of the 1 connected source, or an empty array if no attached source.
        '''
        return self.session().connections.get_all_collections_for_src(self)

    def connection_for_src(self, input_or_mixer, create_if_not_made=False):
        '''
        Given an input or mixer, gets the Connection from it to this.
        If such a Connection has not been made before, makes it.
        '''
        if create_if_not_made:
            return self.session().connections.get_or_add_connection_between_src_and_dest(input_or_mixer, self)
        else:
            return self.session().connections.get_connection_between_src_and_dest(input_or_mixer, self)

    def link_from_source(self):
        '''
        Link this output so that it is receiving AV from the source (mixer).
        '''
        if self.has_video() and self.src().has_video():
            self._connect_tee_to_element(self.src().final_video_tee, 'video')
        if self.has_audio() and self.src().has_audio():
            self._connect_tee_to_element(self.src().final_audio_tee, 'audio')

    def unlink_from_source(self):
        '''
        Stop taking AV from the connected source (mixer).
        '''
        for video_or_audio in ['video', 'audio']:
            if video_or_audio in self.tee_src_pads:
                tee_src_pad = self.tee_src_pads[video_or_audio]
                pad_tee_is_connected_to = tee_src_pad.get_peer()
                if pad_tee_is_connected_to:
                    if tee_src_pad.unlink(pad_tee_is_connected_to):
                        self.logger.debug('Disconnected from tee')
                    else:
                        self.logger.warning('FAILED to disconnect from tee')

    def _sync_elements_on_src_pipeline(self):
        '''
        Make sure the elements on the source (mixer) are matching what the source's state is.
        It's important this happens _after_ after this pipeline has been initialised (i.e. left NULL state),
        so that the caps are correctly discovered.
        '''
        for element_name in ['interaudiosink', 'intervideosink']:
            if hasattr(self, element_name):
                element = getattr(self, element_name)
                if not element.sync_state_with_parent():
                    self.logger.warning('Unable to set %s to state of parent source' % element.name)

        for audio_or_video, element in self._queue_into_intersink.items():
            if not element.sync_state_with_parent():
                self.logger.warning('Unable to set %s to state of parent source' % element.name)

    def delete(self):
        self.logger.info('Being deleted')
        self.unlink_from_source()
        self.__delete_from_source()
        super().delete()

    def __delete_from_source(self):
        for element_name in ['interaudiosink', 'intervideosink']:
            if hasattr(self, element_name):
                element = getattr(self, element_name)
                if not self.src().pipeline.remove(element):
                    self.logger.warning('Unable to remove %s' % element.name)
        # TODO remove src from the source (mixer) tee

    def create_intervideosink_and_connections(self):
        '''
        intervideosink/intervidesrc are used to connect the master pipeline
        with the local pipeline for this output.
        '''
        self.intervideosink = self.src().add_element('intervideosink', self, 'video')

        channel_name = create_intersink_channel_name()
        self.intervideosrc.set_property('channel', channel_name)
        self.intervideosink.set_property('channel', channel_name)

        self._queue_into_intersink['video'] = self.src().add_element('queue', self, 'video', name='video_queue')
        if not self._queue_into_intersink['video'].link(self.intervideosink):
            self.logger.error('Cannot connect queue to intervideosink')

        # We block the source (output) pad of this intervideosrc until we're sure video is being sent.
        # Otherwise the output pipeline will have a 'not negotiated' error if it starts before the other one.
        # We don't need to do this if the other one is playing.
        # Note: without this things work *most* of the time.
        # 'test_image_input' is an example that fails without it.
        if self.src().get_state() not in [Gst.State.PLAYING, Gst.State.PAUSED]:
            block_pad(self, 'intervideosrc_src_pad')

    def create_interaudiosink_and_connections(self):
        '''
        interaudiosink/interaudiosrc are used to connect the master pipeline
        with the local pipeline for this output.
        '''
        self.interaudiosink = self.src().add_element('interaudiosink', self, 'audio')

        channel_name = create_intersink_channel_name()
        self.interaudiosrc.set_property('channel', channel_name)
        self.interaudiosink.set_property('channel', channel_name)

        self._queue_into_intersink['audio'] = self.src().add_element('queue', self, 'audio', name='audio_queue')
        if not self._queue_into_intersink['audio'].link(self.interaudiosink):
            self.logger.error('Cannot connect queue to interaudiosink')

        # We block the source (output) pad of this interaudiosrc until we're sure audio is being sent.
        # Otherwise we can get a partial message, which causes an error.
        # We don't need to do this if the other one is playing.
        if self.src().get_state() not in [Gst.State.PLAYING, Gst.State.PAUSED]:
            block_pad(self, 'interaudiosrc_src_pad')

    def create_caps_string(self):
        '''
        Returns the preferred caps (a string defining things such as width, height and framerate)
        '''

        # Don't set 'format' here... output types set their own.
        caps = 'video/x-raw'

        # If only one dimension is provided, we calculate the other.
        # Some encoders (jpegenc, possibly others) don't like it if only one metric is present.
        width = self.props['width'] if 'width' in self.props else None
        height = self.props['height'] if 'height' in self.props else None
        if self.src():
            src_width, src_height = self.src().get_dimensions()
            if src_width and src_height:
                if width and not height:
                    height = round_down(width * src_height / src_width)
                if height and not width:
                    width = round_down(height * src_width / src_height)
                if not width and not height:
                    width, height = src_width, src_height

        # Some encoders don't like odd-numbered widths:
        if width and width % 2 == 1:
            width += 1

        if width and height:
            caps += ',width=%s,height=%s' % (width, height)

        self.logger.debug('Caps created:' + caps)
        return caps

    def on_pipeline_start(self):
        '''
        Called when the stream starts
        '''
        # We may have blocked pads. This will unblock them, assuming the  is running.
        if self.src() and self.src().get_state() in [Gst.State.PLAYING, Gst.State.PAUSED]:
            unblock_pad(self, 'intervideosrc_src_pad')
            unblock_pad(self, 'interaudiosrc_src_pad')

    def _connect_tee_to_element(self, tee, video_or_audio):
        '''
        Called when it's time to connect an input (via a mixer/tee) to this output
        '''

        # Get the next available source (output) from a tee:
        tee_src_pad_template = tee.get_pad_template("src_%u")
        tee_src_pad = tee.request_pad(tee_src_pad_template, None, None)
        self.logger.debug(f'Connecting {tee.get_name()} request pad ' +
                          f'{tee_src_pad.get_name()} to {video_or_audio}')

        # Keep the source pad so we can disconnect from it later:
        self.tee_src_pads[video_or_audio] = tee_src_pad

        sink = self._queue_into_intersink[video_or_audio].get_static_pad('sink')
        if tee_src_pad.link(sink) != Gst.PadLinkReturn.OK:
            self.logger.error('Failed to connect tee to queue')

    def _set_src(self):
        '''
        Ensure the source of this output (either an input or mixer) is correctly set up.
        '''

        # Default: mixer 0, if it exists:
        if 'mixer_id' not in self.props and 'input_id' not in self.props and 0 in self.session().mixers:
            self.props['mixer_id'] = 0

        if 'mixer_id' in self.props:
            try:
                src = self.session().mixers[self.props['mixer_id']]
            except KeyError as e:
                raise brave.exceptions.InvalidConfiguration('Invalid mixer ID %s' % self.props['mixer_id'])
        elif 'input_id' in self.props:
            try:
                src = self.session().inputs[self.props['input_id']]
            except KeyError as e:
                self.logger.warn('Inputs: %s' % list(self.session().inputs.keys()))
                raise brave.exceptions.InvalidConfiguration('Invalid input ID %s' % self.props['input_id'])
        else:
            self.logger.debug('No source, this output will not show anything')
            return

        connection = self.session().connections.get_or_add_connection_between_src_and_dest(src, self)

    def _video_pipeline_start(self):
        '''
        The standard start to the pipeline string for video.
        It starts with intervideosrc, which accepts video from the source.
        '''
        return ('intervideosrc name=intervideosrc ! videoconvert ! videoscale ! '
                'videorate ! capsfilter name=capsfilter ! ')

    def _audio_pipeline_start(self):
        '''
        The standard start to the pipeline string for audio.
        It starts with interaudiosrc, which accepts audio from the source.
        '''
        return 'interaudiosrc name=interaudiosrc ! audioconvert ! audioresample ! '
