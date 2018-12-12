from gi.repository import Gst
from brave.helpers import create_intersink_channel_name


class Source():
    '''
    A Source is for a Mixer.
    A Source is part of exactly one SourceCollection.
    A Source can be either an Input or another Mixer.
    '''

    def __init__(self, input_or_mixer, collection):
        self.input_or_mixer = input_or_mixer
        self.logger = input_or_mixer.logger
        self.collection = collection
        self.elements_on_mixer_pipeline = []
        self.elements_on_input_pipeline = []
        self.intersrc_src_pad = {}
        self.intersrc_src_pad_probe = {}
        self.tee_pad = {}
        self.tee = {}
        self.mix_request_pad = {}
        self.queue_into_intersink = {}

    def mixer(self):
        '''
        Return the mixer that this source is for
        '''
        return self.collection.mixer

    def cut(self):
        '''
        Cuts to this source (i.e. replaces all other inputs currently showing with the provided one).
        '''
        # Add first, then remove, so we don't have a period of showing the background.
        if not self.in_mix():
            self.add_to_mix()
        for source in self.mixer().sources:
            if source != self:
                source.remove_from_mix()

    def set_mixer_element_state(self, state):
        '''
        Sets all the elements that speifically belong to this source bit of this input
        '''
        for e in self.elements_on_mixer_pipeline:
            if e.set_state(state) != Gst.StateChangeReturn.SUCCESS:
                self.logger.warning('Unable to set mixer element %s to %s state' % (e.name, state.value_nick.upper()))

    def set_input_element_state(self, state):
        '''
        Sets all the elements that speifically belong to this source bit of this input
        '''
        for e in self.elements_on_input_pipeline:
            if e.set_state(state) != Gst.StateChangeReturn.SUCCESS:
                self.logger.warning('Unable to set input element %s to %s state' % (e.name, state.value_nick.upper()))

    def delete(self, callback=None):
        '''
        Deletes this source. Don't get confused with remove_from_mix()
        '''
        self.remove_from_mix()
        self._remove_all_elements()
        self.collection._items.remove(self)
        if callback:
            callback()

    def in_mix(self):
        '''
        Returns True iff this is currently included in the mix
        (and actually showing, not just linked).
        '''
        in_video_mix = 'video' in self.mix_request_pad and \
            self.mix_request_pad['video'].is_linked()
        in_audio_mix = 'audio' in self.mix_request_pad and \
            self.mix_request_pad['audio'].is_linked()
        return in_video_mix or in_audio_mix

    def add_to_mix(self):
        '''
        Places (adds) this input onto the mixer.
        If you want to replace what's on the mix. use source.cut()
        '''
        self._ensure_elements_are_created()
        if self.input_or_mixer.has_video():
            self._add_to_mix('video')
        if self.input_or_mixer.has_audio():
            self._add_to_mix('audio')
        self.unblock_intersrc_if_ready()
        self.mixer().report_update_to_user()

    def remove_from_mix(self):
        '''
        Removes this source from showing on this mixer
        '''
        if self.in_mix():
            if self.input_or_mixer.has_video():
                self._remove_from_mix('video')
            if self.input_or_mixer.has_audio():
                self._remove_from_mix('audio')
            self.logger.debug('Completed removal of from mix.')
            self.mixer().report_update_to_user()

    def handle_updated_props(self):
        '''
        Called after the props have been set/updated, to update the elements
        '''
        if self.input_or_mixer.has_audio():
            self._handle_audio_mix_props()
        if self.input_or_mixer.has_video():
            self._handle_video_mix_props()

    def on_input_pipeline_start(self):
        '''
        Called when the input starts
        '''
        self.unblock_intersrc_if_ready()

    def set_new_caps(self, new_caps):
        if hasattr(self, 'capsfilter_after_intervideosrc'):
            self.capsfilter_after_intervideosrc.set_property('caps', new_caps)
            # caps-change-mode=1 allows the old caps to temporarily exist during the crossover period.
            self.capsfilter_after_intervideosrc.set_property('caps-change-mode', 1)

    def unblock_intersrc_if_ready(self):
        '''
        The intervideosrc and interaudiosrc elements are the bits of the mixer that receive the input.
        They will be blocked when first created, as they can fail if the input is not yet sending content.
        This method unblocks them.
        '''
        if (self.mixer().get_state() in [Gst.State.PLAYING, Gst.State.PAUSED]) and \
           (self.input_or_mixer.get_state() in [Gst.State.PLAYING, Gst.State.PAUSED]) and \
           self._elements_are_created():
            for audio_or_video in ['audio', 'video']:
                if audio_or_video in self.intersrc_src_pad and audio_or_video in self.intersrc_src_pad_probe:
                    self.intersrc_src_pad[audio_or_video].remove_probe(self.intersrc_src_pad_probe[audio_or_video])
                    del self.intersrc_src_pad_probe[audio_or_video]

    def _add_to_mix(self, audio_or_video):
        if audio_or_video in self.mix_request_pad:
            self.logger.info('Request to add to %s mix, but already added' % audio_or_video)
            return

        # We need to conect the tee to the mixer. This is the pad of the tee:
        tee_pad = self._get_or_create_tee_pad(audio_or_video)
        self.mix_request_pad[audio_or_video] = self.mixer().get_new_pad_for_source(audio_or_video)

        link_response = tee_pad.link(self.mix_request_pad[audio_or_video])
        if link_response != Gst.PadLinkReturn.OK:
            self.logger.error('Cannot link %s to mix, response was %s' % (audio_or_video, link_response))

        if audio_or_video == 'audio':
            self._handle_audio_mix_props()
        else:
            self._handle_video_mix_props()

    def _handle_video_mix_props(self):
        '''
        Update the video mixer with the props from this - position on screen, and z-order.
        '''
        if 'video' not in self.mix_request_pad:
            return

        self.mix_request_pad['video'].set_property('xpos', self.input_or_mixer.props['xpos'])
        self.mix_request_pad['video'].set_property('ypos', self.input_or_mixer.props['ypos'])
        self._set_mixer_width_and_height()

        # Setting zorder to what's already set can cause a segfault.
        current_zorder = self.mix_request_pad['video'].get_property('zorder')
        if current_zorder != self.input_or_mixer.props['zorder']:
            self.logger.debug('Setting zorder to %d (current state: %s)' %
                              (self.input_or_mixer.props['zorder'],
                               self.mixer().mixer_element['video'].get_state(0).state.value_nick.upper()))
            self.mix_request_pad['video'].set_property('zorder', self.input_or_mixer.props['zorder'])

    def _handle_audio_mix_props(self):
        '''
        Update the audio mixer with the props from this - just volume at the moment
        '''
        if 'audio' not in self.mix_request_pad:
            return

        prev_volume = self.mix_request_pad['audio'].get_property('volume')
        volume = self.input_or_mixer.props['volume']

        if volume != prev_volume:
            # self.logger.debug(f'Setting volume from {str(prev_volume)} to {str(volume)}')
            self.mix_request_pad['audio'].set_property('volume', float(volume))

    def _set_mixer_width_and_height(self):
        # First stage: go with mixer's size
        width = self.mixer().props['width']
        height = self.mixer().props['height']

        # Second stage: if input is smaller, go with that
        if 'width' in self.input_or_mixer.props and self.input_or_mixer.props['width'] < width:
            width = self.input_or_mixer.props['width']
        if 'height' in self.input_or_mixer.props and self.input_or_mixer.props['height'] < height:
            height = self.input_or_mixer.props['height']

        # Third stage: if positioned to go off the side, reduce the size.
        if width + self.input_or_mixer.props['xpos'] > self.mixer().props['width']:
            width = self.mixer().props['width'] - self.input_or_mixer.props['xpos']
        if height + self.input_or_mixer.props['ypos'] > self.mixer().props['height']:
            height = self.mixer().props['height'] - self.input_or_mixer.props['ypos']

        self.mix_request_pad['video'].set_property('width', width)
        self.mix_request_pad['video'].set_property('height', height)
        self.logger.debug('Setting width and height in mixer to be %s and %s' %
                          (self.mix_request_pad['video'].get_property('width'),
                           self.mix_request_pad['video'].get_property('height')))

    def _create_video_elements(self):
        '''
        Create the 'intervideosrc' element, which accepts the video input that's come from a separate pipeline.
        Then connects intervideosrc to the convert/scale/queue elements, ready for mixing.
        '''
        intervideosrc, intervideosink = self._create_inter_elements('video')
        videoscale = self._add_element_to_mixer_pipeline('videoscale')
        if not intervideosrc.link(videoscale):
            self.logger.error('Cannot link intervideosrc to videoscale')

        # Decent scaling options:
        videoscale.set_property('method', 3)
        videoscale.set_property('dither', True)

        videoconvert = self._add_element_to_mixer_pipeline('videoconvert')
        if not videoscale.link(videoconvert):
            self.logger.error('Cannot link videoscale to videoconvert')

        self.capsfilter_after_intervideosrc = self._add_element_to_mixer_pipeline('capsfilter')
        if not videoconvert.link(self.capsfilter_after_intervideosrc):
            self.logger.error('Cannot link videoconvert to capsfilter')

        queue = self._add_element_to_mixer_pipeline('queue', name='video_queue')

        # We use a tee even though we only have one output (the mixer) because then we can use
        # allow-not-linked which means this bit of the pipeline does not fail when it's disconnected.
        self.tee['video'] = self._add_element_to_mixer_pipeline('tee', name='video_tee_after_queue')
        self.tee['video'].set_property('allow-not-linked', True)

        if not self.capsfilter_after_intervideosrc.link(queue):
            self.logger.error('Cannot link capsfilter to queue')
        if not queue.link(self.tee['video']):
            self.logger.error('Cannot link queue to tee')

    def _create_audio_elements(self):
        '''
        The audio equivalent of _create_video_elements
        '''
        interaudiosrc, interaudiosink = self._create_inter_elements('audio')

        # A queue ensures that disconnection from the audiomixer does not result in a pipeline failure:
        queue = self._add_element_to_mixer_pipeline('queue', name='audio_queue')

        # We use a tee even though we only have one output (the mixer) because then we can use
        # allow-not-linked which means this bit of the pipeline does not fail when it's disconnected.
        self.tee['audio'] = self._add_element_to_mixer_pipeline('tee', name='audio_tee_after_queue')
        self.tee['audio'].set_property('allow-not-linked', True)

        if not interaudiosrc.link(queue):
            self.logger.error('Cannot link interaudiosrc to queue')
        if not queue.link(self.tee['audio']):
            self.logger.error('Cannot link queue to tee')

    def _create_inter_elements(self, audio_or_video):
        '''
        Creates intervideosrc and intervideosink (or the equivalent audio ones)
        '''
        intersrc = self._create_intersrc(audio_or_video)
        intersink = self._create_intersink(audio_or_video)

        # Give the 'inter' elements a channel name. It doesn't matter what, so long as they're unique.
        channel_name = create_intersink_channel_name()
        intersink.set_property('channel', channel_name)
        intersrc.set_property('channel', channel_name)
        return intersrc, intersink

    def _create_intersrc(self, audio_or_video):
        '''
        The intervideosrc/interaudiosrc goes on the destination (mixer) pipeline, so that it
        can accept content from the source pipeline.
        '''
        assert(audio_or_video in ['audio', 'video'])

        # Create the receiving 'inter' element to accept the AV into the main pipeline
        intersrc_element = self._add_element_to_mixer_pipeline('inter%ssrc' % audio_or_video)
        self.intersrc_src_pad[audio_or_video] = intersrc_element.get_static_pad('src')

        # We ask the src to hold the frame for 24 hours (basically, a very long time)
        # This is optional, but prevents it from going black when it's better to show the last frame.
        if audio_or_video is 'video':
            intersrc_element.set_property('timeout', Gst.SECOND * 60 * 60 * 24)

        def _blocked_probe_callback(*_):
            self.logger.debug('_blocked_probe_callback called')
            return Gst.PadProbeReturn.OK

        # We block the source (output) pad of this intervideosrc/interaudiosrc until we're sure video is being sent.
        # Otherwise we can get a partial message, which causes an error.
        self.intersrc_src_pad_probe[audio_or_video] = self.intersrc_src_pad[audio_or_video].add_probe(
            Gst.PadProbeType.BLOCK_DOWNSTREAM, _blocked_probe_callback)

        return intersrc_element

    def _create_intersink(self, audio_or_video):
        '''
        The intervideosink/interaudiosink goes on the source (input/mixer) pipeline, so that it can
        connect to the mixer pipeline.
        '''
        assert(audio_or_video in ['audio', 'video'])
        element_name = 'inter%ssink' % audio_or_video
        input_bin = getattr(self.input_or_mixer, 'final_' + audio_or_video + '_tee').parent
        element = self._add_element_to_input_pipeline(element_name, input_bin=input_bin)
        queue = self._add_element_to_input_pipeline('queue', input_bin=input_bin)
        if not element or not queue:
            return

        self.queue_into_intersink[audio_or_video] = queue

        # Increasing to 3 seconds allows different encoders to share a pipeline.
        # This can be reconsidered if/when outputs are put on different pipelines.
        MAX_SIZE_IN_SECONDS = 3
        queue.set_property('max-size-time', MAX_SIZE_IN_SECONDS * 1000000000)
        queue.set_property('max-size-bytes', MAX_SIZE_IN_SECONDS * 10485760)

        if not queue.link(element):
            self.logger.error('Failed to connect queue to %s' % element_name)

        return element

    def _connect_tee_to_intersink(self, audio_or_video):
        '''
        The tee allows a source to have multiple connections.
        This connects the tee to an intersink (via a queue) so that it can be sent to a mixer.
        '''
        tee = getattr(self.input_or_mixer, 'final_' + audio_or_video + '_tee')
        if not tee:
            self.logger.error('Failed to connect tee to queue: cannot find tee')
            return

        queue = self.queue_into_intersink[audio_or_video]
        if not queue:
            self.logger.error('Failed to connect tee to queue: cannot find queue')
            return

        tee_src_pad_template = tee.get_pad_template("src_%u")
        tee_src_pad = tee.request_pad(tee_src_pad_template, None, None)

        sink = queue.get_static_pad('sink')
        if tee_src_pad.link(sink) != Gst.PadLinkReturn.OK:
            self.logger.error('Failed to connect tee to queue')

    def _remove_from_mix(self, audio_or_video):
        if (not self.mix_request_pad[audio_or_video].is_linked()):
            self.logger.info('Attempted to remove from %s mix but not currently mixed' % audio_or_video)
            return

        if audio_or_video in self.mix_request_pad:
            self.mix_request_pad[audio_or_video].get_peer().unlink(self.mix_request_pad[audio_or_video])
            # After unlinking, if we don't remove the pad, the final frame remains in the mix:
            self.mixer().mixer_element[audio_or_video].release_request_pad(self.mix_request_pad[audio_or_video])
            del self.mix_request_pad[audio_or_video]

    def _remove_all_elements(self):
        '''
        Remove all elements for this rouce, which will be partly on the mixer and partly on the input.
        '''
        self.set_mixer_element_state(Gst.State.NULL)
        for e in self.elements_on_mixer_pipeline:
            if not e.get_parent().remove(e):
                self.collection.mixer.logger.warning('Unable to remove %s' % e.name)

        self.set_input_element_state(Gst.State.NULL)
        for e in self.elements_on_input_pipeline:
            if not e.get_parent().remove(e):
                self.logger.warning('Unable to remove %s' % e.name)

    def _add_element_to_mixer_pipeline(self, factory_name, name=None):
        '''
        Add an element on the mixer's pipeline, on behalf of this source
        '''
        e = self.collection.mixer.add_element(factory_name, self.input_or_mixer, name)
        self.elements_on_mixer_pipeline.append(e)
        return e

    def _add_element_to_input_pipeline(self, factory_name, input_bin, name=None):
        '''
        Add an element on the mixer's pipeline, on behalf of this source
        '''
        e = Gst.ElementFactory.make(factory_name, name)
        if not input_bin.add(e):
            self.logger.error('Unable to add element %s' % factory_name)
            return None
        self.elements_on_input_pipeline.append(e)
        return e

    def _sync_element_states(self):
        '''
        Make sure the elements created on the source and destination have their state set to match their pipeline.
        '''
        for e in self.elements_on_mixer_pipeline:
            if not e.sync_state_with_parent():
                self.logger.warning('Unable to set %s to state of parent source' % e.name)
        for e in self.elements_on_input_pipeline:
            if not e.sync_state_with_parent():
                self.logger.warning('Unable to set %s to state of parent source' % e.name)

    def _elements_are_created(self):
        return (not self.input_or_mixer.has_video() or hasattr(self, 'video_is_linked')) and \
               (not self.input_or_mixer.has_audio() or hasattr(self, 'audio_is_linked'))

    def _ensure_elements_are_created(self):
        # STEP 1: Connect the input (or source mixer) and the mixer, unless that's already been done
        if self.input_or_mixer.has_video() and not hasattr(self, 'video_is_linked'):
            self._create_video_elements()
        if self.input_or_mixer.has_audio() and not hasattr(self, 'audio_is_linked'):
            self._create_audio_elements()

        # STEP 2: Get the new elements in the same state as their pipelines:
        self._sync_element_states()

        # STEP 3: Connect the input's tee to these new elements
        # (It's important we don't do this earlier, as if the elements were not
        #  ready we could disrupt the existing pipeline.)
        if self.input_or_mixer.has_video() and not hasattr(self, 'video_is_linked'):
            self._connect_tee_to_intersink('video')
            self.video_is_linked = True
        if self.input_or_mixer.has_audio() and not hasattr(self, 'audio_is_linked'):
            self._connect_tee_to_intersink('audio')
            self.audio_is_linked = True

        # If input and mixer have already started, we need to unblock straightaway:
        self.unblock_intersrc_if_ready()

    def _get_or_create_tee_pad(self, audio_or_video):
        if audio_or_video in self.tee_pad:
            return self.tee_pad[audio_or_video]
        else:
            tee_src_pad_template = self.tee[audio_or_video].get_pad_template("src_%u")
            self.tee_pad[audio_or_video] = self.tee[audio_or_video].request_pad(tee_src_pad_template, None, None)
            return self.tee_pad[audio_or_video]
