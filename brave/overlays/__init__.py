from brave.overlays.text import TextOverlay
from brave.overlays.effect import EffectOverlay
from brave.overlays.clock import ClockOverlay
from brave.abstract_collection import AbstractCollection
from gi.repository import Gst
import brave.exceptions
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('brave.overlays')


class OverlayCollection(AbstractCollection):
    '''
    This is the collection of all created overlays.
    An overlay can be text or clock.
    '''

    def add(self, **args):
        args['id'] = self.get_new_id()

        if 'type' not in args:
            raise brave.exceptions.InvalidConfiguration("Invalid output missing 'type'")
        elif args['type'] == 'text':
            overlay = TextOverlay(**args, collection=self)
        elif args['type'] == 'effect':
            overlay = EffectOverlay(**args, collection=self)
        elif args['type'] == 'clock':
            overlay = ClockOverlay(**args, collection=self)
        else:
            raise brave.exceptions.InvalidConfiguration("Invalid overlay type '%s'" % args['type'])

        self._items[args['id']] = overlay
        return overlay

    def ensure_overlays_are_correctly_connected(self, mixer):
        '''
        Ensure the provided mixer's pipeline contains the correct overlay elements.
        '''
        def _connect_overlays_once_blocked(*_):
            '''
            Called once the video is blocked, this arranges all the overlays in the pipeline.
            '''

            def getSortValue(overlay):
                return overlay.getSortValue()

            overlays = sorted(list(filter(lambda o: o.visible and o.mixer() == mixer, self._items.values())),
                              key=getSortValue)

            if len(overlays) == 0:
                if not _link_if_not_already_linked(mixer.video_mixer_output_queue,
                                                   mixer.end_capsfilter):
                    mixer.logger.warn('Unable to connect from video mixer output queue to me')
            else:
                # The first should be linked to from the video mixer
                if not _link_if_not_already_linked(mixer.video_mixer_output_queue,
                                                   overlays[0].element):
                    overlays[0].logger.warn('Unable to connect from video mixer to me')

                # Connect the middle ones together:
                for n in range(len(overlays) - 1):
                    if not _link_if_not_already_linked(overlays[n].element, overlays[n + 1].element):
                        overlays[n].logger.warn('Unable to connect to the next overlay ' + str(overlays[n + 1]))

                # The last should be linked to the video mixer tee
                logger.debug('Now linking overlay %s to the video mixer tee' % overlays[-1].id)
                if not _link_if_not_already_linked(overlays[-1].element, mixer.end_capsfilter):
                    overlays[-1].logger.warn('Unable to connect to the video mixer tee')

            #  Unblock everything
            for overlay in overlays:
                overlay.ensure_src_pad_not_blocked()

            logger.debug('Completed update of overlays, now unblocking')
            return Gst.PadProbeReturn.REMOVE

        # We block the video so that we can make changes to a live pipeline
        # As described at https://gstreamer.freedesktop.org/documentation/design/ ...
        # ... probes.html#dynamically-switching-an-element-in-a-playing-pipeline
        if mixer.get_state() in [Gst.State.PLAYING, Gst.State.PAUSED]:
            logger.debug('Overlays need updating, blocking pipeline temporarily')
            self.video_mixer_queue_src_pad = mixer.video_mixer_output_queue.get_static_pad('src')
            self.video_mixer_queue_src_pad_block_probe = self.video_mixer_queue_src_pad.add_probe(
                Gst.PadProbeType.BLOCK_DOWNSTREAM, _connect_overlays_once_blocked)
        else:
            _connect_overlays_once_blocked()


def _link_if_not_already_linked(element1, element2):

    # First, make sure element1 isn't linked to anything (except perhaps element2)
    element1_check = ensure_pad_not_linked(element1, 'src', correct_linked_element=element2)
    if not element1_check['success']:
        return False
    if element1_check['already_linked']:
        return True

    # Second, make sure element2 isn't linked to anything
    element2_check = ensure_pad_not_linked(element2, 'sink')
    if not element2_check['success']:
        return False

    # Finally, do the link
    logger.debug('Linking %s to %s' % (element1.get_name(), element2.get_name()))
    if not element1.link(element2):
        logger.warn('Cannot link %s to %s' % (element1.get_name(), element2.get_name()))
        return False
    return True


def ensure_pad_not_linked(element, pad_name, correct_linked_element=None):
    '''
    Given an element and pad name, ensures it is not linked to anything.
    Optionally, if correct_linked_element is provided, that element is permitted to be linked.
    '''
    pad = element.get_static_pad(pad_name)

    # TODO can we handle this nicer:
    if not pad and pad_name == 'sink':
        pad = element.get_static_pad('video_sink')

    if not pad:
        logger.warn('Cannot get %s pad of element %s to confirm it is not linked' % (pad_name, element.get_name()))
        return {'success': False}

    if not pad.is_linked():
        return {'success': True, 'already_linked': False}

    peer = pad.get_peer()
    if not peer:
        logger.warn('Cannot unlink %s of %s, no peer pad' % (pad_name, element.get_name()))
        return {'success': False}

    if correct_linked_element:
        peer_element = peer.get_parent_element()
        if peer_element == correct_linked_element:
            logger.debug('Already linked %s and %s, nothing to do' %
                         (element.get_name(), correct_linked_element.get_name()))
            return {'success': True, 'already_linked': True}

    if pad_name == 'sink':
        unlink_response = peer.unlink(pad)
    else:
        unlink_response = pad.unlink(peer)
    if unlink_response:
        logger.debug('Unlinked %s pad of %s from %s' %
                     (pad_name, element.get_name(), peer.get_parent_element().get_name()))
        return {'success': True, 'already_linked': False}

    logger.warn('Unable to unlink %s pad of %s' % (pad_name, element.get_name()))
    return {'success': False}
