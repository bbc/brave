from gi.repository import Gst
from brave.helpers import create_intersink_channel_name
from brave.mixers.mixer import Mixer

class Connection():
    '''
    A connection connects a 'src' to a 'dest'. Valid connections are:
     - input to mixer
     - mixer to mixer
     - input to output
     - mixer to output
    '''

    def __init__(self, **args):
        for a in args:
            setattr(self, a, args[a])
        self.logger = self.src.logger

        self._elements_on_dest_pipeline = []
        self._elements_on_src_pipeline = []
        self._intersrc_src_pad = {}
        self._intersrc_src_pad_probe = {}
        self._tee_pad = {}
        self._tee = {}
        self._queue_into_intersink = {}

    def delete(self, callback=None):
        '''
        Deletes this connection. Don't get confused with remove_from_mix()
        '''
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
        The intervideosrc and interaudiosrc elements are the bits of the destination that receive the input.
        They will be blocked when first created, as they can fail if the input is not yet sending content.
        This method unblocks them.
        '''
        if (self.dest.get_state() in [Gst.State.PLAYING, Gst.State.PAUSED]) and \
           (self.src.get_state() in [Gst.State.PLAYING, Gst.State.PAUSED]) and \
           self._elements_are_created():
            for audio_or_video in ['audio', 'video']:
                if audio_or_video in self._intersrc_src_pad and audio_or_video in self._intersrc_src_pad_probe:
                    self._intersrc_src_pad[audio_or_video].remove_probe(self._intersrc_src_pad_probe[audio_or_video])
                    del self._intersrc_src_pad_probe[audio_or_video]

    def _create_video_elements(self):
        '''
        Create the 'intervideosrc' element on the destination pipeline.
        This will accept the video input that's come from the source pipeline.
        The intervideosrc is connected to convert/scale/queue elements.
        '''
        intervideosrc, intervideosink = self._create_inter_elements('video')
        videoscale = self._add_element_to_dest_pipeline('videoscale')
        if not intervideosrc.link(videoscale):
            self.logger.error('Cannot link intervideosrc to videoscale')

        # Decent scaling options:
        videoscale.set_property('method', 3)
        videoscale.set_property('dither', True)

        videoconvert = self._add_element_to_dest_pipeline('videoconvert')
        if not videoscale.link(videoconvert):
            self.logger.error('Cannot link videoscale to videoconvert')

        self.capsfilter_after_intervideosrc = self._add_element_to_dest_pipeline('capsfilter')
        if not videoconvert.link(self.capsfilter_after_intervideosrc):
            self.logger.error('Cannot link videoconvert to capsfilter')

        queue = self._add_element_to_dest_pipeline('queue', name='video_queue')

        # We use a tee even though we only have one output because then we can use
        # allow-not-linked which means this bit of the pipeline does not fail when it's disconnected.
        # TODO reconsider this
        self._tee['video'] = self._add_element_to_dest_pipeline('tee', name='video_tee_after_queue')
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
        queue = self._add_element_to_dest_pipeline('queue', name='audio_queue')

        # We use a tee even though we only have one output because then we can use
        # allow-not-linked which means this bit of the pipeline does not fail when it's disconnected.
        self._tee['audio'] = self._add_element_to_dest_pipeline('tee', name='audio_tee_after_queue')
        self._tee['audio'].set_property('allow-not-linked', True)

        if not interaudiosrc.link(queue):
            self.logger.error('Cannot link interaudiosrc to queue')
        if not queue.link(self._tee['audio']):
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
        The intervideosrc/interaudiosrc goes on the destination (mixer/output) pipeline, so that it
        can accept content from the source pipeline.
        '''
        assert(audio_or_video in ['audio', 'video'])

        # Create the receiving 'inter' element to accept the AV into the main pipeline
        intersrc_element = self._add_element_to_dest_pipeline('inter%ssrc' % audio_or_video)
        self._intersrc_src_pad[audio_or_video] = intersrc_element.get_static_pad('src')

        # We ask the src to hold the frame for 24 hours (basically, a very long time)
        # This is optional, but prevents it from going black when it's better to show the last frame.
        if audio_or_video is 'video':
            intersrc_element.set_property('timeout', Gst.SECOND * 60 * 60 * 24)

        def _blocked_probe_callback(*_):
            self.logger.debug('_blocked_probe_callback called')
            return Gst.PadProbeReturn.OK

        # We block the source (output) pad of this intervideosrc/interaudiosrc until we're sure video is being sent.
        # Otherwise we can get a partial message, which causes an error.
        self._intersrc_src_pad_probe[audio_or_video] = self._intersrc_src_pad[audio_or_video].add_probe(
            Gst.PadProbeType.BLOCK_DOWNSTREAM, _blocked_probe_callback)

        return intersrc_element

    def _create_intersink(self, audio_or_video):
        '''
        The intervideosink/interaudiosink goes on the source (input/mixer) pipeline, to then connect to the destination.
        '''
        assert(audio_or_video in ['audio', 'video'])
        element_name = 'inter%ssink' % audio_or_video
        input_bin = getattr(self.src, 'final_' + audio_or_video + '_tee').parent
        element = self._add_element_to_src_pipeline(element_name, input_bin=input_bin)
        queue = self._add_element_to_src_pipeline('queue', input_bin=input_bin)
        if not element or not queue:
            return

        self._queue_into_intersink[audio_or_video] = queue

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
        This connects the tee to an intersink (via a queue) so that it can be sent to a destination.
        '''
        tee = getattr(self.src, 'final_' + audio_or_video + '_tee')
        if not tee:
            self.logger.error('Failed to connect tee to queue: cannot find tee')
            return

        queue = self._queue_into_intersink[audio_or_video]
        if not queue:
            self.logger.error('Failed to connect tee to queue: cannot find queue')
            return

        tee_src_pad_template = tee.get_pad_template("src_%u")
        tee_src_pad = tee.request_pad(tee_src_pad_template, None, None)

        sink = queue.get_static_pad('sink')
        if tee_src_pad.link(sink) != Gst.PadLinkReturn.OK:
            self.logger.error('Failed to connect tee to queue')

    def _remove_all_elements(self):
        '''
        Remove all elements for this source. They will be split among the source and destination pipelines.
        '''
        self._set_dest_element_state(Gst.State.NULL)
        for e in self._elements_on_dest_pipeline:
            if not e.get_parent().remove(e):
                self.dest.logger.warning('Unable to remove %s' % e.name)

        self._set_src_element_state(Gst.State.NULL)
        for e in self._elements_on_src_pipeline:
            if not e.get_parent().remove(e):
                self.logger.warning('Unable to remove %s' % e.name)

    def _add_element_to_dest_pipeline(self, factory_name, name=None):
        '''
        Add an element on the destination pipeline
        '''
        e = self.dest.add_element(factory_name, self.src, name)
        self._elements_on_dest_pipeline.append(e)
        return e

    def _add_element_to_src_pipeline(self, factory_name, input_bin, name=None):
        '''
        Add an element on the source pipeline
        '''
        e = Gst.ElementFactory.make(factory_name, name)
        if not input_bin.add(e):
            self.logger.error('Unable to add element %s' % factory_name)
            return None
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
        return (not self.src.has_video() or hasattr(self, 'video_is_linked')) and \
               (not self.src.has_audio() or hasattr(self, 'audio_is_linked'))

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

    def _get_or_create_tee_pad(self, audio_or_video):
        if audio_or_video in self._tee_pad:
            return self._tee_pad[audio_or_video]
        else:
            tee_src_pad_template = self._tee[audio_or_video].get_pad_template("src_%u")
            self._tee_pad[audio_or_video] = self._tee[audio_or_video].request_pad(tee_src_pad_template, None, None)
            return self._tee_pad[audio_or_video]

    def _set_dest_element_state(self, state):
        '''
        Set the state of all elements on the dest pipeline
        '''
        for e in self._elements_on_dest_pipeline:
            if e.set_state(state) != Gst.StateChangeReturn.SUCCESS:
                self.dest.logger.warning('Unable to set element %s to %s state' % (e.name, state.value_nick.upper()))

    def _set_src_element_state(self, state):
        '''
        Set the state of all elements on the src pipeline
        '''
        for e in self._elements_on_src_pipeline:
            if e.set_state(state) != Gst.StateChangeReturn.SUCCESS:
                self.logger.warning('Unable to set input element %s to %s state' % (e.name, state.value_nick.upper()))
