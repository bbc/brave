from gi.repository import Gst
from brave.helpers import create_intersink_channel_name, block_pad, unblock_pad


class Connection():
    '''
    A connection connects a 'source' to a 'dest'. Valid connections are:
     - input to mixer
     - mixer to mixer
     - input to output
     - mixer to output
    '''

    def __init__(self, **args):
        for a in args:
            setattr(self, a, args[a])
        self.logger = self.source.logger

        self._elements_on_dest_pipeline = []
        self._elements_on_src_pipeline = []
        self._queue_into_intersink = {}

    def delete(self, callback=None):
        '''
        Deletes this connection. Don't get confused with remove_from_mix()
        '''
        # Before removing elements, unlink from the source.
        if self.has_video():
            self._block_intersrc('video')
            self._unlink_from_src_tee('video')
        if self.has_audio():
            self._block_intersrc('audio')
            self._unlink_from_src_tee('audio')

        self._remove_all_elements()
        self.collection.pop(self.id)
        if callback:
            callback()

    def handle_updated_props(self):
        '''
        Called after the props have been set/updated, to update the elements
        '''
        pass
        # overwritten by subclass

    def set_new_caps(self, new_caps):
        if hasattr(self, 'capsfilter_after_intervideosrc'):
            self.capsfilter_after_intervideosrc.set_property('caps', new_caps)
            # caps-change-mode=1 allows the old caps to temporarily exist during the crossover period.
            self.capsfilter_after_intervideosrc.set_property('caps-change-mode', 1)

    def unblock_intersrc_if_ready(self):
        '''
        The intervideosrc and interaudiosrc elements are the bits of the destination that receive the input.
        They will be blocked when first created, as they can fail if the input is not yet sending content.
        This method unblocks them.
        '''
        if (self.dest.state in [Gst.State.PLAYING, Gst.State.PAUSED]) and \
           (self.source.state in [Gst.State.PLAYING, Gst.State.PAUSED]) and \
           self._elements_are_created():
            for audio_or_video in ['audio', 'video']:
                pad = self._get_intersrc_src_pad(audio_or_video)
                if pad:
                    unblock_pad(pad)

    def has_video(self):
        '''
        True iff both the src and dest have video
        '''
        return self.source.has_video() and self.dest.has_video()

    def has_audio(self):
        '''
        True iff both the src and dest have audio
        '''
        return self.source.has_audio() and self.dest.has_audio()

    def summarise(self):
        return {
            'uid': self.source.uid,
            'in_mix': self.in_mix()
        }

    def _get_intersrc_src_pad(self, audio_or_video):
        element = self._get_intersrc(audio_or_video)
        return element.get_static_pad('src') if element else None

    def _create_inter_elements(self, audio_or_video):
        '''
        Creates intervideosrc and intervideosink (or the equivalent audio ones)
        '''
        intersrc = self._create_intersrc(audio_or_video)
        intersink = self._create_intersink(audio_or_video)
        self._block_intersrc(audio_or_video)

        # Give the 'inter' elements a channel name. It doesn't matter what, so long as they're unique.
        channel_name = create_intersink_channel_name()
        if intersink:
            intersink.set_property('channel', channel_name)
        if intersrc:
            intersrc.set_property('channel', channel_name)
        return intersrc, intersink

    def _block_intersrc(self, audio_or_video):
        '''
        The intersrc (into the dest pipeline) is blocked until it's definitely got a source.
        '''
        def _blocked_probe_callback(*_):
            self.logger.debug('_blocked_probe_callback called')
            return Gst.PadProbeReturn.OK

        # We block the source (output) pad of this intervideosrc/interaudiosrc until we're sure video
        # is being sent. Otherwise we can get a partial message, which causes an error.
        block_pad(self._get_intersrc_src_pad(audio_or_video))

    def _create_intersink(self, audio_or_video):
        '''
        The intervideosink/interaudiosink goes on the source (input/mixer) pipeline, to then connect to the destination.
        '''
        assert(audio_or_video in ['audio', 'video'])
        element_name = 'inter%ssink' % audio_or_video
        element = self._add_element_to_src_pipeline(element_name, audio_or_video)
        queue = self._add_element_to_src_pipeline('queue', audio_or_video, name=audio_or_video + '_queue')
        if not element or not queue:
            return

        self._queue_into_intersink[audio_or_video] = queue

        if not queue.link(element):
            self.logger.error('Failed to connect queue to %s' % element_name)

        return element

    def _connect_tee_to_intersink(self, audio_or_video):
        '''
        The tee allows a source to have multiple connections to multiple destinations.
        This method links tee -> queue -> intersink, so that it can be sent to a destination.
        '''
        tee = getattr(self.source, 'final_' + audio_or_video + '_tee')
        if not tee:
            self.logger.error('Failed to connect tee to queue: cannot find tee')
            return

        tee_src_pad_template = tee.get_pad_template("src_%u")
        tee_src_pad = tee.request_pad(tee_src_pad_template, None, None)

        sink = self._get_pad_to_connect_tee_to(audio_or_video)
        if not sink or tee_src_pad.link(sink) != Gst.PadLinkReturn.OK:
            self.logger.error('Failed to connect tee to queue')

    def _unlink_from_src_tee(self, audio_or_video):
        '''
        This connection is connected to the source via a 'tee' element.
        This method disconnects from that tee.
        '''
        pad = self._get_pad_to_connect_tee_to(audio_or_video)
        if not pad:
            self.logger.warning('Cannot unlink from tee: cannot find connected pad')
            return
        tee_pad = pad.get_peer()
        if not tee_pad:
            self.logger.warning('Cannot unlink from tee: cannot find connected tee pad')
            return
        tee_pad.unlink(pad)

        # Now delete the pad, we won't need it again
        tee_pad.get_parent().release_request_pad(tee_pad)

    def _get_pad_to_connect_tee_to(self, audio_or_video):
        '''
        Returns the pad of the queue that should be connected to from the source's 'tee' element.
        '''
        queue = self._queue_into_intersink[audio_or_video]
        if not queue:
            self.logger.error('Failed to connect tee to queue: cannot find queue')
            return

        return queue.get_static_pad('sink')

    def _remove_all_elements(self):
        '''
        Remove all elements for this source. They will be split among the source and destination pipelines.
        '''
        self._set_dest_element_state(Gst.State.NULL)
        for e in self._elements_on_dest_pipeline:
            if not e.get_parent().remove(e):
                self.dest.logger.warning('Unable to remove %s' % e.name)

        self._set_source_element_state(Gst.State.NULL)
        for e in self._elements_on_src_pipeline:
            if not e.get_parent().remove(e):
                self.logger.warning('Unable to remove %s' % e.name)

    def _add_element_to_dest_pipeline(self, factory_name, audio_or_video, name=None):
        '''
        Add an element on the destination pipeline
        '''
        e = self.dest.add_element(factory_name, self.source, audio_or_video=audio_or_video, name=name)
        self._elements_on_dest_pipeline.append(e)
        return e

    def _add_element_to_src_pipeline(self, factory_name, audio_or_video, name=None):
        '''
        Add an element on the source pipeline
        '''
        e = self.source.add_element(factory_name, self.dest, audio_or_video=audio_or_video, name=name)
        self._elements_on_src_pipeline.append(e)
        return e

    def _sync_element_states(self):
        '''
        Make sure the elements created on the source and destination have their state set to match their pipeline.
        '''
        for e in self._elements_on_dest_pipeline:
            if not e.sync_state_with_parent():
                self.logger.warning('Unable to set %s to state of parent source' % e.name)
        for e in self._elements_on_src_pipeline:
            if not e.sync_state_with_parent():
                self.logger.warning('Unable to set %s to state of parent source' % e.name)

    def _elements_are_created(self):
        return (not self.has_video() or hasattr(self, 'video_is_linked')) and \
               (not self.has_audio() or hasattr(self, 'audio_is_linked'))

    def _set_dest_element_state(self, state):
        '''
        Set the state of all elements on the dest pipeline
        '''
        for e in self._elements_on_dest_pipeline:
            if e.set_state(state) != Gst.StateChangeReturn.SUCCESS:
                self.dest.logger.warning('Unable to set element %s to %s state' % (e.name, state.value_nick.upper()))

    def _set_source_element_state(self, state):
        '''
        Set the state of all elements on the src pipeline
        '''
        for e in self._elements_on_src_pipeline:
            if e.set_state(state) != Gst.StateChangeReturn.SUCCESS:
                self.logger.warning('Unable to set input element %s to %s state' % (e.name, state.value_nick.upper()))
