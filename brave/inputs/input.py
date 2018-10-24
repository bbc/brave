import traceback
from gi.repository import Gst, GLib
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

        # Create the receiving 'inter' element to accept the AV into the main pipeline
        intervideosrc = self.session().mixers[0].add_element_for_source('intervideosrc', self)
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

        videoscale = self.session().mixers[0].add_element_for_source('videoscale', self)
        intervideosrc.link(videoscale)

        # Decent scaling options:
        videoscale.set_property('method', 3)
        videoscale.set_property('dither', True)

        self.capsfilter_after_intervideosrc = self.session().mixers[0].add_element_for_source('capsfilter', self)
        videoscale.link(self.capsfilter_after_intervideosrc)

        queue = self.session().mixers[0].add_element_for_source('queue', self, name='video_queue')
        self.capsfilter_after_intervideosrc.link(queue)

        self.video_pad_to_connect_to_mix = queue.get_static_pad('src')

    def create_interaudiosrc_and_connections(self):
        '''
        The audio equivalent of create_intervideosrc_and_connections
        '''
        # Create the receiving 'inter' elements to accept the AV into the main pipeline
        interaudiosrc = self.session().mixers[0].add_element_for_source('interaudiosrc', self)
        self.interaudiosrc_src_pad = interaudiosrc.get_static_pad('src')

        # Blocks the src pad to stop incomplete messages.
        # Note, this has caused issues in the past.
        self._block_interaudiosrc_src_pad()

        # Give the 'inter' elements a channel name. It doesn't matter what, so long as they're unique.
        channel_name = create_intersink_channel_name()
        self.interaudiosink.set_property('channel', channel_name)
        interaudiosrc.set_property('channel', channel_name)

        self.audio_pad_to_connect_to_mix = interaudiosrc.get_static_pad('src')

    def delete(self):
        self.logger.info('Being deleted')
        super_delete = super().delete

        def after_remove_from_mix():
            self.session().mixers[0].sources.delete_for_input_or_mixer(self)
            super_delete()

        self.remove_from_mix(callback=after_remove_from_mix)

    def in_mix(self):
        '''
        Returns True iff this is currently includded in the mix
        (and actually showing, not just linked).
        '''
        in_video_mix = hasattr(self, 'video_pad_to_connect_to_mix') and \
            self.video_pad_to_connect_to_mix.is_linked()
        in_audio_mix = hasattr(self, 'audio_pad_to_connect_to_mix') and \
            self.audio_pad_to_connect_to_mix.is_linked()
        return in_video_mix or in_audio_mix

    def add_to_mix(self):
        '''
        Places (adds) this input onto the mix.
        If you want to replace what's on the mix. use mixer.cut_to_source()
        '''
        self.logger.debug('Overlaying to mixer')
        if self.has_video():
            self._add_video_to_mix()
        if self.has_audio():
            self._add_audio_to_mix()
        self._unblock_mix_pads()

        # If previously removed from the mix, the state will be forced NULL.
        # This sets it back to that of hte main pipeline:
        my_mixer_source = self.session().mixers[0].sources.get_for_input_or_mixer(self)
        if my_mixer_source:
            my_mixer_source.set_element_state(self.session().mixers[0].pipeline.get_state(0).state)
        else:
            self.logger.warn('Cannot find my mixer source to add, should not be possible')

        self.session().mixers[0].report_update_to_user()

    def _add_video_to_mix(self):
        # 'video_pad_to_connect_to_mix' may not exist for test_video if the
        # decoder hasn't kicked in
        if not hasattr(self, 'video_pad_to_connect_to_mix'):
            return

        if (self.video_pad_to_connect_to_mix.is_linked()):
            self.logger.info('Attempted to add to mix when already there')
            return

        if hasattr(self, 'video_mix_request_pad'):
            traceback.print_stack()
            self.logger.warn('Already have video_mix_request_pad, should not be possible')

        self.video_mix_request_pad = self.session().mixers[0].get_video_mixer_request_pad(self)
        if (self.video_pad_to_connect_to_mix.is_linked()):
            self.logger.info('Attempted to add to video mix when already there')
            return

        self._handle_video_mix_props()
        print('****** TEMP CRASH DISCOVERY: linking input to mix STARTING')
        print('****** TEMP CRASH DISCOVERY:  linking input to mix self.video_pad_to_connect_to_mix=',
              self.video_pad_to_connect_to_mix)
        print('****** TEMP CRASH DISCOVERY:  linking input to mix self.video_mix_request_pad=',
              self.video_mix_request_pad)
        self.video_pad_to_connect_to_mix.link(self.video_mix_request_pad)
        print('****** TEMP CRASH DISCOVERY:  linking input to mix COMPLETE')

    def _add_audio_to_mix(self):
        if hasattr(self, 'audio_pad_to_connect_to_mix') and self.audio_pad_to_connect_to_mix.is_linked():
            self.logger.info('Attempted to add to mix when already there')
            return

        if hasattr(self, 'audio_mix_request_pad'):
            self.logger.warn('Already have audio_mix_request_pad, should not be possible')

        self.audio_mix_request_pad = self.session().mixers[0].get_audio_mixer_request_pad(self)
        if (self.audio_pad_to_connect_to_mix.is_linked()):
            self.logger.info('Attempted to add to audio mix when already there')
            return

        self.audio_pad_to_connect_to_mix.link(self.audio_mix_request_pad)
        self._handle_audio_mix_props()

    def remove_from_mix(self, callback=None):
        if not self.in_mix():
            if callback:
                callback()
            return

        def _set_my_mixer_elements_to_null():
            my_mixer_source = self.session().mixers[0].sources.get_for_input_or_mixer(self)
            if my_mixer_source:
                my_mixer_source.set_element_state(Gst.State.NULL)
            else:
                self.logger.warn('Cannot find my mixer source to remove, should not be possible')

            self.logger.info('Completed removal of input ' + str(self.id) + ' from mix.')
            self.session().mixers[0].report_update_to_user()
            if callback:
                callback()

        def _after_removal_from_both_mixes():
            # We set the state of these elements to NULL because we don't need them running.
            # But one of the elements (queue) is the one that this callback is for.
            # So we cannot directly set the state or else a deadlock will occur.
            # Instead, we ask the GLib event look to do this at the next idle moment.
            GLib.idle_add(_set_my_mixer_elements_to_null)
            self.logger.debug('Completed removal of input ' + str(self.id) + ' from mix, except setting state to NULL.')

        def _after_removal_from_video_mix():
            if self.has_audio():
                self._remove_from_audio_mix(_after_removal_from_both_mixes)
            else:
                _after_removal_from_both_mixes()

        if self.has_video():
            self._remove_from_video_mix(_after_removal_from_video_mix)
        else:
            _after_removal_from_video_mix()

    def _remove_from_video_mix(self, callback):
        if (not self.video_pad_to_connect_to_mix.is_linked()):
            self.logger.info('Attempted to remove from mix when not in video mix')
            callback()
            return

        on_blocked_function_called = False

        def _remove_from_video_mix_now_blocked(*_):
            nonlocal on_blocked_function_called
            if on_blocked_function_called:
                return Gst.PadProbeReturn.OK
            on_blocked_function_called = True

            if hasattr(self, 'video_mix_request_pad'):
                # First, unlink this input from the mixer:
                self.video_pad_to_connect_to_mix.unlink(self.video_mix_request_pad)
                # Then, tell the mixer to remove the request (input) pad
                self.session().mixers[0].video_mixer.release_request_pad(self.video_mix_request_pad)
                delattr(self, 'video_mix_request_pad')
            callback()

            # We must keep the block in place as the elements are still in PLAYING state:
            return Gst.PadProbeReturn.OK

        self.video_pad_to_mix_probe = self.video_pad_to_connect_to_mix.add_probe(
            Gst.PadProbeType.BLOCKING, _remove_from_video_mix_now_blocked, None)

    def _remove_from_audio_mix(self, callback):
        if (not self.audio_pad_to_connect_to_mix.is_linked()):
            self.logger.info('Attempted to remove from mix when not in audio mix')
            callback()
            return

        on_blocked_function_called = False

        def _remove_from_audio_mix_now_blocked(*_):
            nonlocal on_blocked_function_called
            if on_blocked_function_called:
                return Gst.PadProbeReturn.OK
            on_blocked_function_called = True

            if hasattr(self, 'audio_mix_request_pad'):
                self.audio_pad_to_connect_to_mix.unlink(self.audio_mix_request_pad)
                self.session().mixers[0].audio_mixer.release_request_pad(self.audio_mix_request_pad)
                delattr(self, 'audio_mix_request_pad')
            callback()

            # We must keep the block in place as the elements are still in PLAYING state:
            return Gst.PadProbeReturn.OK

        self.audio_pad_to_mix_probe = self.audio_pad_to_connect_to_mix.add_probe(
            Gst.PadProbeType.BLOCKING, _remove_from_audio_mix_now_blocked)

    def handle_updated_props(self):
        '''
        Called after the props have been set/updated, to update the elements
        '''
        if self.has_audio():
            self._handle_audio_mix_props()
        if self.has_video():
            self._update_video_filter_caps()
            self._handle_video_mix_props()

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

        # if mix_height and mix_width:
        #     if width and not height:
        #         height = round_down(width * mix_height / mix_width)
        #     if height and not width:
        #         width = round_down(height * mix_width / mix_height)
        #     if not width and not height:
        #         width, height = mix_width, mix_height
        #     if width > mix_width or height > mix_height:
        #         width, height = mix_width, mix_height

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

    def _handle_video_mix_props(self):
        '''
        Update the video mixer with the props from this - position on screen, and z-order.
        '''
        if not hasattr(self, 'video_mix_request_pad'):
            return

        self.video_mix_request_pad.set_property('xpos', self.props['xpos'])
        self.video_mix_request_pad.set_property('ypos', self.props['ypos'])
        self._set_mixer_width_and_height()

        # Setting zorder to what's already set can cause a segfault.
        current_zorder = self.video_mix_request_pad.get_property('zorder')
        if current_zorder != self.props['zorder']:
            self.logger.debug('Setting zorder to ' + str(self.props['zorder']) +
                              ' (current state:' +
                              self.session().mixers[0].video_mixer.get_state(0).state.value_nick.upper() + ')')
            self.video_mix_request_pad.set_property('zorder', self.props['zorder'])

    def _set_mixer_width_and_height(self):
        mixer = self.session().mixers[0]

        # First stage: go with mixer's size
        width = mixer.props['width']
        height = mixer.props['height']

        # Second stage: if input is smaller, go with that
        if 'width' in self.props and self.props['width'] < width:
            width = self.props['width']
        if 'height' in self.props and self.props['height'] < height:
            height = self.props['height']

        # Third stage: if positioned to go off the side, reduce the size.
        if width + self.props['xpos'] > mixer.props['width']:
            width = mixer.props['width'] - self.props['xpos']
        if height + self.props['ypos'] > mixer.props['height']:
            height = mixer.props['height'] - self.props['ypos']

        self.video_mix_request_pad.set_property('width', width)
        self.video_mix_request_pad.set_property('height', height)
        self.logger.debug('Setting width and height in mixer to be %s and %s' %
                          (self.video_mix_request_pad.get_property('width'),
                           self.video_mix_request_pad.get_property('height')))

    def _handle_audio_mix_props(self):
        '''
        Update the audio mixer with the props from this - just volume at the moment
        '''
        if not hasattr(self, 'audio_mix_request_pad'):
            return

        prev_volume = self.audio_mix_request_pad.get_property('volume')
        volume = self.props['volume']

        if volume != prev_volume:
            # self.logger.debug(f'Setting volume from {str(prev_volume)} to {str(volume)}')
            self.audio_mix_request_pad.set_property('volume', float(volume))

    def _unblock_mix_pads(self):
        '''
        Mix pads will have been blocked if previously removed from a mix. This unblocks them.
        '''
        if hasattr(self, 'video_pad_to_mix_probe'):
            self.video_pad_to_connect_to_mix.remove_probe(self.video_pad_to_mix_probe)
            delattr(self, 'video_pad_to_mix_probe')
            self.logger.info('Remove block from video mix pad')
        if hasattr(self, 'audio_pad_to_mix_probe'):
            self.audio_pad_to_connect_to_mix.remove_probe(self.audio_pad_to_mix_probe)
            delattr(self, 'audio_pad_to_mix_probe')
            self.logger.info('Remove block from audio mix pad')

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
