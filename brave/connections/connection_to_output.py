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

        self._link_source_to_dest()
        self._sync_element_states()

        if self.has_video():
            self.video_is_linked = True
        if self.has_audio():
            self.audio_is_linked = True

        # If source and destination have already started, we need to unblock straightaway:
        self.unblock_intersrc_if_ready()

    def _get_intersrc(self, audio_or_video):
        '''
        Return the intervideosrc/interaudiosrc that the output pipeline has for accepting content.
        '''
        assert(audio_or_video in ['audio', 'video'])
        element_name = 'inter%ssrc' % audio_or_video
        return getattr(self.dest, element_name) if hasattr(self.dest, element_name) else None

    def _create_intersrc(self, audio_or_video):
        '''
        The intervideosrc/interaudiosrc will already be made by the output, so no need to make again.
        '''
        return self._get_intersrc(audio_or_video)

    def _link_source_to_dest(self):
        '''
        Link the source (input/mixer) to the dest (output).
        '''
        if self.has_video():
            self._connect_tee_to_intersink('video')
        if self.has_audio():
            self._connect_tee_to_intersink('audio')
