from gi.repository import Gst
from brave.helpers import round_down, create_intersink_channel_name
from brave.inputoutputoverlay import InputOutputOverlay


class Output(InputOutputOverlay):
    '''
    An abstract superclass representing an output.
    '''

    def __init__(self, **args):
        super().__init__(**args)

        # In the future, we can have more varied sources:
        self.source = self.session().mixers[self.props['mixer_id']]

        self.create_elements()

        # This stores the pads on the source's tee which are connected to this output:
        self.tee_src_pads = {}

        # Set initially to READY, and when there we set to self.props['initial_state']
        self.pipeline.set_state(Gst.State.READY)

    def input_output_overlay_or_mixer(self):
        return 'output'

    def permitted_props(self):
        return {
            **super().permitted_props(),
            'mixer_id': {
                'type': 'int',
                'default': 0
            }
        }

    def _create_initial_multiqueue(self):
        '''
        Every output has a multiqueue on the the source (mixer) pipeline.
        tee -> multiqueue -> intervideosink (or audio) -> intervideosrc (or audio)
        '''
        # The entry point for all outputs is a single multiqueue.
        self.multiqueue = self.source.add_element('multiqueue', self)

        # Increasing to 3 seconds allows different encoders to share a pipeline.
        # This can be reconsidered if/when outputs are put on different pipelines.
        MAX_SIZE_IN_SECONDS = 3
        self.multiqueue.set_property('max-size-time', MAX_SIZE_IN_SECONDS * 1000000000)
        self.multiqueue.set_property('max-size-bytes', MAX_SIZE_IN_SECONDS * 10485760)

    def link_from_source(self):
        '''
        Link this output so that it is receiving AV from the source (mixer).
        '''
        if self.has_video():
            self._connect_tee_to_element(self.source.final_video_tee, 'video')
        if self.has_audio():
            self._connect_tee_to_element(self.source.final_audio_tee, 'audio')

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
                        self.logger.warn('FAILED to disconnect from tee')

    def _sync_elements_on_source_pipeline(self):
        '''
        Make sure the elements on the source (mixer) are matching what the source's state is.
        It's important this happens _after_ after this pipeline has been initialised (i.e. left NULL state),
        so that the caps are correctly discovered.
        '''
        for element_name in ['multiqueue', 'interaudiosink', 'intervideosink']:
            if hasattr(self, element_name):
                element = getattr(self, element_name)
                if not element.sync_state_with_parent():
                    self.logger.warn('Unable to set %s to state of parent source' % element.name)

    def delete(self):
        self.logger.info('Being deleted')
        self.unlink_from_source()
        self.__delete_from_source()
        super().delete()

    def __delete_from_source(self):
        for element_name in ['multiqueue', 'interaudiosink', 'intervideosink']:
            if hasattr(self, element_name):
                element = getattr(self, element_name)
                if not self.source.pipeline.remove(element):
                    self.logger.warn('Unable to remove %s' % element.name)
        # TODO remove src from the source (mixer) tee

    def create_intervideosink_and_connections(self):
        '''
        intervideosink/intervidesrc are used to connect the master pipeline
        with the local pipeline for this output.
        '''
        self.intervideosink = self.source.add_element('intervideosink', self)
        self.video_element_multiqueue_should_connect_to = self.intervideosink

        channel_name = create_intersink_channel_name()
        self.intervideosrc.set_property('channel', channel_name)
        self.intervideosink.set_property('channel', channel_name)

        # We block the source (output) pad of this intervideosrc until we're sure video is being sent.
        # Otherwise the output pipeline will have a 'not negotiated' error if it starts before the other one.
        # We don't need to do this if the other one is playing.
        # Note: without this things work *most* of the time.
        # 'test_image_input' is an example that fails without it.
        if self.source.get_state() not in [Gst.State.PLAYING, Gst.State.PAUSED]:
            self._block_intervideosrc_src_pad()

    def create_interaudiosink_and_connections(self):
        '''
        interaudiosink/interaudiosrc are used to connect the master pipeline
        with the local pipeline for this output.
        '''
        self.interaudiosink = self.source.add_element('interaudiosink', self)
        self.audio_element_multiqueue_should_connect_to = self.interaudiosink

        channel_name = create_intersink_channel_name()
        self.interaudiosrc.set_property('channel', channel_name)
        self.interaudiosink.set_property('channel', channel_name)

        # We block the source (output) pad of this interaudiosrc until we're sure audio is being sent.
        # Otherwise we can get a partial message, which causes an error.
        # We don't need to do this if the other one is playing.
        if self.source.get_state() not in [Gst.State.PLAYING, Gst.State.PAUSED]:
            self._block_interaudiosrc_src_pad()

    def create_caps_string(self):
        '''
        Returns the preferred caps (a string defining things such as width, height and framerate)
        '''
        caps = 'video/x-raw'

        # If only one dimension is provided, we calculate the other.
        # Some encoders (jpegenc, possibly others) don't like it if only one metric is present.
        width = self.props['width'] if 'width' in self.props else None
        height = self.props['height'] if 'height' in self.props else None
        mix_width, mix_height = self.source.get_dimensions()
        if mix_width and mix_height:
            if width and not height:
                height = round_down(width * mix_height / mix_width)
            if height and not width:
                width = round_down(height * mix_width / mix_height)
            if not width and not height:
                width, height = mix_width, mix_height

        # Some encoders don't like odd-numbered widths:
        if width % 2 == 1:
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
        if self.source.get_state() in [Gst.State.PLAYING, Gst.State.PAUSED]:
            self.unblock_intervideosrc_src_pad()
            self.unblock_interaudiosrc_src_pad()

    def _multiqueue_pad_added(self, element, pad):
        '''
        Called when the multiqueue gets a pad added.
        The job of this is to handle the src (output) pad and connect it to the next thing.
        '''
        if pad.get_direction() != Gst.PadDirection.SRC:
            return
        if pad.is_linked():
            return
        name = pad.get_name()
        if (name == 'src_0'):
            video_or_audio = 'video'
        elif name == 'src_1':
            video_or_audio = 'audio'
        else:
            raise ValueError('Value not video or audio')

        if video_or_audio == 'video':
            sink_pad_to_link_to = self.video_element_multiqueue_should_connect_to.get_static_pad('sink')
            if pad.link(sink_pad_to_link_to) != Gst.PadLinkReturn.OK:
                self.logger.warn('Failed to connect multiqueue (video) to',
                                 self.video_element_multiqueue_should_connect_to)

        elif video_or_audio == 'audio':
            sink_pad_to_link_to = self.audio_element_multiqueue_should_connect_to.get_static_pad('sink')
            if pad.link(sink_pad_to_link_to) != Gst.PadLinkReturn.OK:
                self.logger.warn('Failed to connect multiqueue (audio) to',
                                 self.audio_element_multiqueue_should_connect_to)

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

        # This output has a multiqueue as its first entry point:
        self.multiqueue.connect('pad-added', self._multiqueue_pad_added)

        # Multiqueue has as many ins and outs as you want. There's no convention
        # afaik, so let's go with 0 for video and 1 for audio.
        if video_or_audio == 'video':
            sinkName = 'sink_0'
        elif video_or_audio == 'audio':
            sinkName = 'sink_1'
        else:
            raise ValueError('Value not video or audio')

        sink = self.multiqueue.get_request_pad(sinkName)
        if tee_src_pad.link(sink) != Gst.PadLinkReturn.OK:
            self.logger.error('Failed to connect tee pad')
