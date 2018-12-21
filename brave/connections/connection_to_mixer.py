from gi.repository import Gst
from brave.connections.connection import Connection


class ConnectionToMixer(Connection):
    '''
    A connection from an input/mixer to a mixer.
    '''

    def __init__(self, **args):
        super().__init__(**args)
        self._mix_request_pad = {}
        self._tee_pad = {}
        self._tee = {}
        self._intersrc_src_pad_probe_dict = {}

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

        if 'xpos' in self.src.props:
            self._mix_request_pad['video'].set_property('xpos', self.src.props['xpos'])
        if 'ypos' in self.src.props:
            self._mix_request_pad['video'].set_property('ypos', self.src.props['ypos'])
        self._set_mixer_width_and_height()

        # Setting zorder to what's already set can cause a segfault.
        if 'zorder' in self.src.props:
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

        if 'volume' in self.src.props:
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
        if 'xpos' in self.src.props:
            if width + self.src.props['xpos'] > self.dest.props['width']:
                width = self.dest.props['width'] - self.src.props['xpos']
        if 'ypos' in self.src.props:
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

    def _ensure_elements_are_created(self):
        # STEP 1: Connect the source to the destination, unless that's already been done
        if self.src.has_video() and not hasattr(self, 'video_is_linked'):
            self._create_video_elements()
        if self.src.has_audio() and not hasattr(self, 'audio_is_linked'):
            self._create_audio_elements()

        # STEP 2: Get the new elements in the same state as their pipelines:
        self._sync_element_states()

        # STEP 3: Connect the input's tee to these new elements
        # (It's important we don't do this earlier, as if the elements were not
        #  ready we could disrupt the existing pipeline.)
        if self.src.has_video() and not hasattr(self, 'video_is_linked'):
            self._connect_tee_to_intersink('video')
            self.video_is_linked = True
        if self.src.has_audio() and not hasattr(self, 'audio_is_linked'):
            self._connect_tee_to_intersink('audio')
            self.audio_is_linked = True

        # If source and destination have already started, we need to unblock straightaway:
        self.unblock_intersrc_if_ready()

    def _create_video_elements(self):
        '''
        Create the elements to connect the src and dest pipelines.
        Src pipeline looks like: tee -> queue -> intervideosink
        Dest pipeline looks like: intervideosrc -> videoscale -> videoconvert -> capsfilter -> queue -> tee
        '''
        intervideosrc, intervideosink = self._create_inter_elements('video')
        self._create_dest_elements_after_intervideosrc(intervideosrc)

    def _create_dest_elements_after_intervideosrc(self, intervideosrc):
        '''
        On the destination pipeline, after the intervideosrc, we scale/convert the video so that we can
        set the relevant caps. This method provides theose elements.
        '''
        videoscale = self._add_element_to_dest_pipeline('videoscale', 'video')
        if not intervideosrc.link(videoscale):
            self.logger.error('Cannot link intervideosrc to videoscale')

        # Decent scaling options:
        videoscale.set_property('method', 3)
        videoscale.set_property('dither', True)

        videoconvert = self._add_element_to_dest_pipeline('videoconvert', 'video')
        if not videoscale.link(videoconvert):
            self.logger.error('Cannot link videoscale to videoconvert')

        self.capsfilter_after_intervideosrc = self._add_element_to_dest_pipeline('capsfilter', 'video')
        if not videoconvert.link(self.capsfilter_after_intervideosrc):
            self.logger.error('Cannot link videoconvert to capsfilter')

        queue = self._add_element_to_dest_pipeline('queue', 'video', name='video_queue')

        # We use a tee even though we only have one output because then we can use
        # allow-not-linked which means this bit of the pipeline does not fail when it's disconnected.
        # TODO reconsider this
        self._tee['video'] = self._add_element_to_dest_pipeline('tee', 'video', name='video_tee_after_queue')
        self._tee['video'].set_property('allow-not-linked', True)

        if not self.capsfilter_after_intervideosrc.link(queue):
            self.logger.error('Cannot link capsfilter to queue')
        if not queue.link(self._tee['video']):
            self.logger.error('Cannot link queue to tee')

    def _create_audio_elements(self):
        '''
        The audio equivalent of _create_video_elements
        '''
        interaudiosrc, interaudiosink = self._create_inter_elements('audio')

        # A queue ensures that disconnection from the audiomixer does not result in a pipeline failure:
        queue = self._add_element_to_dest_pipeline('queue', 'audio', name='audio_queue')

        # We use a tee even though we only have one output because then we can use
        # allow-not-linked which means this bit of the pipeline does not fail when it's disconnected.
        self._tee['audio'] = self._add_element_to_dest_pipeline('tee', 'audio', name='audio_tee_after_queue')
        self._tee['audio'].set_property('allow-not-linked', True)

        if not interaudiosrc.link(queue):
            self.logger.error('Cannot link interaudiosrc to queue')
        if not queue.link(self._tee['audio']):
            self.logger.error('Cannot link queue to tee')

    def _create_intersrc(self, audio_or_video):
        '''
        The intervideosrc/interaudiosrc goes on the destination (mixer/output) pipeline, so that it
        can accept content from the source pipeline.
        '''
        assert(audio_or_video in ['audio', 'video'])

        # Create the receiving 'inter' element to accept the AV into the main pipeline
        intersrc_element = self._add_element_to_dest_pipeline('inter%ssrc' % audio_or_video, audio_or_video)

        # We ask the src to hold the frame for 24 hours (basically, a very long time)
        # This is optional, but prevents it from going black when it's better to show the last frame.
        if audio_or_video is 'video':
            intersrc_element.set_property('timeout', Gst.SECOND * 60 * 60 * 24)

        return intersrc_element

    def _intersrc_src_pad_probe(self):
        return self._intersrc_src_pad_probe_dict
