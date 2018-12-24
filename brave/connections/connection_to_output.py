from brave.connections.connection import Connection


class ConnectionToOutput(Connection):
    '''
    A connection from an input/mixer to an output.
    '''
    def setup(self):
        if self.has_video():
            self._create_inter_elements('video')

        if self.has_audio():
            self._create_inter_elements('audio')

        self._link_src_to_dest()
        self._sync_element_states()

        if self.has_video():
            self.video_is_linked = True
        if self.has_audio():
            self.audio_is_linked = True

        # If source and destination have already started, we need to unblock straightaway:
        self.unblock_intersrc_if_ready()

    def _create_intersrc(self, audio_or_video):
        '''
        The intervideosrc/interaudiosrc will already be made by the output, so return it.
        '''
        assert(audio_or_video in ['audio', 'video'])
        return getattr(self.dest, 'inter%ssrc' % audio_or_video)

    def _link_src_to_dest(self):
        '''
        Link the src (input/mixer) to the dest (output).
        '''
        if self.has_video():
            self._connect_tee_to_intersink('video')
        if self.has_audio():
            self._connect_tee_to_intersink('audio')

    def _intersrc_src_pad_probe(self):
        return self.dest.intersrc_src_pad_probe
