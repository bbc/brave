from gi.repository import Gst
from brave.connections import Connection


class ConnectionToMixer(Connection):
    '''
    A type of connection for going into a mixer.
    It differs in that is can be mixed.
    '''

    def __init__(self, **args):
        super().__init__(**args)
        self._mix_request_pad = {}

    def delete(self, callback=None):
        '''
        Deletes this connection. Don't get confused with remove_from_mix()
        '''
        self.remove_from_mix()
        super().delete(callback)

    def cut(self):
        if not self.in_mix():
            self.add_to_mix()
        for src in self.dest.src_connections():
            if src != self:
                src.remove_from_mix()

    def in_mix(self):
        '''
        Returns True iff this is currently included in the mix
        (and actually showing, not just linked).
        '''
        in_video_mix = 'video' in self._mix_request_pad and \
            self._mix_request_pad['video'].is_linked()
        in_audio_mix = 'audio' in self._mix_request_pad and \
            self._mix_request_pad['audio'].is_linked()
        return in_video_mix or in_audio_mix

    def add_to_mix(self):
        '''
        Places (adds) this input onto the mixer.
        If you want to replace what's on the mix. use source.cut()
        '''
        self._ensure_elements_are_created()
        if self.src.has_video():
            self._add_to_mix('video')
        if self.src.has_audio():
            self._add_to_mix('audio')
        self.unblock_intersrc_if_ready()
        self.dest.report_update_to_user()

    def remove_from_mix(self):
        '''
        Removes this source from showing on this mixer
        '''
        if self.in_mix():
            if self.src.has_video():
                self._remove_from_mix('video')
            if self.src.has_audio():
                self._remove_from_mix('audio')
            self.logger.debug('Completed removal of from mix.')
            self.dest.report_update_to_user()

    def handle_updated_props(self):
        '''
        Called after the props have been set/updated, to update the elements
        '''
        # Note: overwrites parent method
        if self.src.has_audio():
            self._handle_audio_mix_props()
        if self.src.has_video():
            self._handle_video_mix_props()

    def _add_to_mix(self, audio_or_video):
        if audio_or_video in self._mix_request_pad:
            self.logger.info('Request to add to %s mix, but already added' % audio_or_video)
            return

        # We need to conect the tee to the destination. This is the pad of the tee:
        tee_pad = self._get_or_create_tee_pad(audio_or_video)
        self._mix_request_pad[audio_or_video] = self.dest.get_new_pad_for_source(audio_or_video)

        link_response = tee_pad.link(self._mix_request_pad[audio_or_video])
        if link_response != Gst.PadLinkReturn.OK:
            self.logger.error('Cannot link %s to mix, response was %s' % (audio_or_video, link_response))

        if audio_or_video == 'audio':
            self._handle_audio_mix_props()
        else:
            self._handle_video_mix_props()

    def _handle_video_mix_props(self):
        '''
        Set properties about the video mix
        '''
        if 'video' not in self._mix_request_pad:
            return

        self._mix_request_pad['video'].set_property('xpos', self.src.props['xpos'])
        self._mix_request_pad['video'].set_property('ypos', self.src.props['ypos'])
        self._set_mixer_width_and_height()

        # Setting zorder to what's already set can cause a segfault.
        current_zorder = self._mix_request_pad['video'].get_property('zorder')
        if current_zorder != self.src.props['zorder']:
            self.logger.debug('Setting zorder to %d (current state: %s)' %
                              (self.src.props['zorder'],
                               self.dest.mixer_element['video'].get_state(0).state.value_nick.upper()))
            self._mix_request_pad['video'].set_property('zorder', self.src.props['zorder'])

    def _handle_audio_mix_props(self):
        '''
        Update the audio mixer with the props from this - just volume at the moment
        '''
        if 'audio' not in self._mix_request_pad:
            return

        prev_volume = self._mix_request_pad['audio'].get_property('volume')
        volume = self.src.props['volume']

        if volume != prev_volume:
            # self.logger.debug(f'Setting volume from {str(prev_volume)} to {str(volume)}')
            self._mix_request_pad['audio'].set_property('volume', float(volume))

    def _set_mixer_width_and_height(self):
        # First stage: go with mixer's size
        width = self.dest.props['width']
        height = self.dest.props['height']

        # Second stage: if input is smaller, go with that
        if 'width' in self.src.props and self.src.props['width'] < width:
            width = self.src.props['width']
        if 'height' in self.src.props and self.src.props['height'] < height:
            height = self.src.props['height']

        # Third stage: if positioned to go off the side, reduce the size.
        if width + self.src.props['xpos'] > self.dest.props['width']:
            width = self.dest.props['width'] - self.src.props['xpos']
        if height + self.src.props['ypos'] > self.dest.props['height']:
            height = self.dest.props['height'] - self.src.props['ypos']

        self._mix_request_pad['video'].set_property('width', width)
        self._mix_request_pad['video'].set_property('height', height)
        self.logger.debug('Setting width and height in mixer to be %s and %s' %
                          (self._mix_request_pad['video'].get_property('width'),
                           self._mix_request_pad['video'].get_property('height')))

    def _remove_from_mix(self, audio_or_video):
        if (not self._mix_request_pad[audio_or_video].is_linked()):
            self.logger.info('Attempted to remove from %s mix but not currently mixed' % audio_or_video)
            return

        if audio_or_video in self._mix_request_pad:
            self._mix_request_pad[audio_or_video].get_peer().unlink(self._mix_request_pad[audio_or_video])
            # After unlinking, if we don't remove the pad, the final frame remains in the mix:
            self.dest.mixer_element[audio_or_video].release_request_pad(self._mix_request_pad[audio_or_video])
            del self._mix_request_pad[audio_or_video]

    def _get_or_create_tee_pad(self, audio_or_video):
        if audio_or_video in self._tee_pad:
            return self._tee_pad[audio_or_video]
        else:
            tee_src_pad_template = self._tee[audio_or_video].get_pad_template("src_%u")
            self._tee_pad[audio_or_video] = self._tee[audio_or_video].request_pad(tee_src_pad_template, None, None)
            return self._tee_pad[audio_or_video]
