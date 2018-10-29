from gi.repository import Gst
from brave.helpers import create_intersink_channel_name
from brave.inputoutputoverlay import InputOutputOverlay


class Input(InputOutputOverlay):
    '''
    An abstract superclass representing an AV input.
    '''

    def __init__(self, **args):
        super().__init__(**args)
        self.session().mixers[0].sources.add(self)
        self.create_elements()

    def input_output_overlay_or_mixer(self):
        return 'input'

    def summarise(self):
        s = super().summarise()

        if hasattr(self, 'pipeline'):
            s['position'] = int(str(self.pipeline.query_position(Gst.Format.TIME).cur))
            s['duration'] = int(str(self.pipeline.query_duration(Gst.Format.TIME).duration))

            has_connection_speed, _, _ = self.pipeline.lookup('connection-speed')
            if has_connection_speed:
                s['connection_speed'] = self.pipeline.get_property('connection-speed')
            has_buffer_size, _, _ = self.pipeline.lookup('buffer-size')
            if has_buffer_size:
                s['buffer_size'] = self.pipeline.get_property('buffer-size')
            has_buffer_duration, _, _ = self.pipeline.lookup('buffer-duration')
            if has_buffer_duration:
                s['buffer_duration'] = self.pipeline.get_property('buffer-duration')

            # playbin will respond with duration=-1 when not known.
            if (s['duration'] == -1):
                s.pop('duration', None)

        if hasattr(self, 'get_input_cap_props'):
            cap_props = self.get_input_cap_props()
            if cap_props:
                s = {**s, **cap_props}

        return s

    def create_intervideosrc_and_connections(self):
        '''
        Create the 'intervideosrc' element, which accepts the video input that's come from a separate pipeline.
        Then connects intervideosrc to the convert/scale/queue elements, ready for mixing.
        '''

        mixer = self.session().mixers[0]

        source = mixer.sources.get_for_input_or_mixer(self)
        if not source:
            raise Exception('Cannot find source for input %d with mixer %d' % (self.id, mixer.id))

        # Create the receiving 'inter' element to accept the AV into the main pipeline
        intervideosrc = source.add_element('intervideosrc')
        self.intervideosrc_src_pad = intervideosrc.get_static_pad('src')

        # We ask the src to hold the frame for 24 hours (basically, a very long time)
        # This is optional, but prevents it from going black when it's better to show the last frame.
        intervideosrc.set_property('timeout', Gst.SECOND * 60 * 60 * 24)

        # We block the source (output) pad of this intervideosrc until we're sure video is being sent.
        # Otherwise we can get a partial message, which causes an error.
        self._block_intervideosrc_src_pad()

        # Give the 'inter' elements a channel name. It doesn't matter what, so long as they're unique.
        channel_name = create_intersink_channel_name()
        self.intervideosink.set_property('channel', channel_name)
        intervideosrc.set_property('channel', channel_name)

        videoscale = source.add_element('videoscale')
        intervideosrc.link(videoscale)

        # Decent scaling options:
        videoscale.set_property('method', 3)
        videoscale.set_property('dither', True)

        self.capsfilter_after_intervideosrc = source.add_element('capsfilter')
        videoscale.link(self.capsfilter_after_intervideosrc)

        queue = source.add_element('queue', name='video_queue')
        self.capsfilter_after_intervideosrc.link(queue)

        self.video_pad_to_connect_to_mix = queue.get_static_pad('src')

    def create_interaudiosrc_and_connections(self):
        '''
        The audio equivalent of create_intervideosrc_and_connections
        '''

        mixer = self.session().mixers[0]

        source = mixer.sources.get_for_input_or_mixer(self)
        if not source:
            raise Exception('Cannot find source for input %d with mixer %d' % (self.id, mixer.id))

        # Create the receiving 'inter' elements to accept the AV into the main pipeline
        interaudiosrc = source.add_element('interaudiosrc')
        self.interaudiosrc_src_pad = interaudiosrc.get_static_pad('src')

        # Blocks the src pad to stop incomplete messages.
        # Note, this has caused issues in the past.
        self._block_interaudiosrc_src_pad()

        # Give the 'inter' elements a channel name. It doesn't matter what, so long as they're unique.
        channel_name = create_intersink_channel_name()
        self.interaudiosink.set_property('channel', channel_name)
        interaudiosrc.set_property('channel', channel_name)

        self.audio_pad_to_connect_to_mix = interaudiosrc.get_static_pad('src')

    def sources(self):
        '''
        Returns all the Source instances that are for this input.
        (There will be one for every mixer instance.)
        '''
        sources = []
        for name, mixer in self.session().mixers.items():
            sources.append(mixer.sources.get_for_input_or_mixer(self))
        return [x for x in sources if x is not None]

    def delete(self):
        self.logger.info('Being deleted')
        super_delete = super().delete
        sources = self.sources()

        def iterate_through_sources():
            if len(sources) == 0:
                super_delete()
            else:
                source = sources.pop()
                source.delete(callback=iterate_through_sources)

        iterate_through_sources()

    def handle_updated_props(self):
        '''
        Called after the props have been set/updated, to update the elements
        '''
        if self.has_video():
            self._update_video_filter_caps()
            for source in self.sources():
                source.handle_updated_props()

    def _create_caps_string(self):
        '''
        Returns the preferred caps (a string defining things such as width, height and framerate)
        '''
        width = self.props['width'] if 'width' in self.props else 0
        height = self.props['height'] if 'height' in self.props else 0
        mixer = self.session().mixers[0]

        mix_width, mix_height = None, None
        if mixer:
            mix_width, mix_height = mixer.get_dimensions()

        if not width or not height:
            caps_string = 'video/x-raw,pixel-aspect-ratio=1/1'
        else:
            caps_string = 'video/x-raw,width=%d,height=%d,pixel-aspect-ratio=1/1' % (width, height)

        self.logger.debug('caps_string=%s' % caps_string)
        return caps_string

    def _update_video_filter_caps(self):
        caps_string = self._create_caps_string()
        if caps_string is None:
            return
        self.logger.debug('New caps: ' + caps_string)
        new_caps = Gst.Caps.from_string(caps_string)

        if hasattr(self, 'capsfilter'):
            self.capsfilter.set_property('caps', new_caps)

        # We have a second capsfilter after the jump between pipelines.
        # We must also set that to be the same caps.
        if hasattr(self, 'capsfilter_after_intervideosrc'):
            self.capsfilter_after_intervideosrc.set_property('caps', new_caps)
            # caps-change-mode=1 allows the old caps to temporarily exist during the crossover period.
            self.capsfilter_after_intervideosrc.set_property('caps-change-mode', 1)

    def on_pipeline_start(self):
        '''
        Called when the stream starts
        '''
        self._unblock_intersrc_if_mixer_is_ready()

    def _unblock_intersrc_if_mixer_is_ready(self):
        mixer = self.session().mixers[0]
        if mixer.get_state() in [Gst.State.PLAYING, Gst.State.PAUSED]:
            self.unblock_intervideosrc_src_pad()
            self.unblock_interaudiosrc_src_pad()
        # otherwise, mixer will unblock when it does start.
