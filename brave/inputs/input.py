from gi.repository import Gst
from brave.inputoutputoverlay import InputOutputOverlay


class Input(InputOutputOverlay):
    '''
    An abstract superclass representing an AV input.
    '''

    def setup(self):
        '''
        Sets up the relevant GStreamer pipeline for this input.
        '''
        self.create_elements()
        self.handle_updated_props()

        # Set initially to READY, and when there we set to self.props['initial_state']
        self.set_state(Gst.State.READY)

    def input_output_overlay_or_mixer(self):
        return 'input'

    def dest_connections(self):
        '''
        Returns an array of Connections, describing what this input is connected to.
        (An input can have any number of connections, each going to a Mixer or Output.)
        '''
        return self.session().connections.get_all_collections_for_src(self)

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

    def handle_updated_props(self):
        '''
        Called after the props have been set/updated, to update the elements
        '''
        if self.has_video():
            self._update_video_filter_caps()
            for connection in self.dest_connections():
                connection.handle_updated_props()

    def _create_caps_string(self):
        '''
        Returns the preferred caps (a string defining things such as width, height and framerate)
        '''
        width = self.props['width'] if 'width' in self.props else 0
        height = self.props['height'] if 'height' in self.props else 0
        # TODO can we work without this mixer:
        # mixer = self.session().mixers[0]

        mix_width, mix_height = None, None
        # if mixer:
        #     mix_width, mix_height = mixer.get_dimensions()

        # An internal format of 'RGBA' ensures alpha support and no color variation.
        # It then may be set to something else on output (e.g. I420)
        caps_string = 'video/x-raw,pixel-aspect-ratio=1/1,format=RGBA'
        if width and height:
            caps_string += ',width=%d,height=%d' % (width, height)

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
        for connection in self.dest_connections():
            connection.set_new_caps(new_caps)

    def on_pipeline_start(self):
        '''
        Called when the stream starts
        '''
        for connection in self.dest_connections():
            connection.unblock_intersrc_if_ready()

    def default_video_pipeline_string_end(self):
        # A tee is used so that we can connect this input to multiple mixers/outputs
        return ' ! tee name=final_video_tee allow-not-linked=true'

    def default_audio_pipeline_string_end(self):
        # A tee is used so that we can connect this input to multiple mixers/outputs
        return ' ! tee name=final_audio_tee allow-not-linked=true'

    def add_element(self, factory_name, who_its_for, audio_or_video, name=None):
        '''
        Add an element on the pipeline belonging to this mixer.
        Note: this method's interface matches mixer.add_element()
        '''
        if name is None:
            name = factory_name
        name = who_its_for.input_output_overlay_or_mixer() + '_' + str(who_its_for.id) + '_' + name
        input_bin = getattr(self, 'final_' + audio_or_video + '_tee').parent
        e = Gst.ElementFactory.make(factory_name, name)
        if not input_bin.add(e):
            self.logger.error('Unable to add element %s' % factory_name)
            return None
        return e
