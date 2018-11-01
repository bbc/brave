from gi.repository import Gst
from brave.inputoutputoverlay import InputOutputOverlay


class Input(InputOutputOverlay):
    '''
    An abstract superclass representing an AV input.
    '''

    def __init__(self, **args):
        super().__init__(**args)
        self.create_elements()
        self.set_state(Gst.State.READY)

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
        for source in self.sources():
            source.set_new_caps(new_caps)

    def on_pipeline_start(self):
        '''
        Called when the stream starts
        '''
        for source in self.sources():
            source.on_input_pipeline_start()

    def default_video_pipeline_string_end(self):
        return ' ! tee name=final_video_tee allow-not-linked=true'

    def default_audio_pipeline_string_end(self):
        return ' ! tee name=final_audio_tee allow-not-linked=true'
