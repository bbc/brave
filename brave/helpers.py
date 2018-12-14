import logging
import os
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib


def get_logger(name, format=None):
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO').upper())
    if format:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(format))
        logger.addHandler(handler)
    return logger


def state_string_to_constant(str):
    str = str.upper()
    if (str == 'PLAYING'):
        return Gst.State.PLAYING
    if (str == 'PAUSED'):
        return Gst.State.PAUSED
    if (str == 'READY'):
        return Gst.State.READY
    if (str == 'NULL'):
        return Gst.State.NULL
    return None


def round_down(n):
    return round(n - 0.5)


channel_count = 0


def create_intersink_channel_name():
    '''
    Simply creates a guaranteed unique channel ID for pairing the inter (audio/video) sink/src
    '''
    global channel_count
    channel_count += 1
    return 'inter_channel_' + str(channel_count)


def get_pipeline_details(pipeline, show_inside_bin_elements=True):
    '''
    Given a GStreamer pipeline, returns an object of details about itself.
    This is used for debugging.
    '''
    elements = []

    def handle_each_element(element, parent_element=None):
        details = {
            'name': element.name,
            'state': element.get_state(0).state.value_nick.upper(),
            'pads': {}
        }

        if parent_element is not None:
            details['parent'] = parent_element.name

        if element.get_factory() is not None:
            details['type'] = element.get_factory().name

            inter_elements = ['interaudiosrc', 'interaudiosink', 'intervideosrc', 'intervideosink']
            if details['type'] in inter_elements:
                details['channel'] = element.get_property('channel')
            if details['type'] == 'queue':
                details['current-level-time'] = element.get_property('current-level-time')

        def handle_pad(pad):
            details['pads'][pad.name] = {
                'blocked': pad.is_blocked(),
                'blocking': pad.is_blocking(),
                'active': pad.is_active(),
            }

            caps = pad.get_current_caps()
            if caps:
                size = caps.get_size()
                if size > 0:
                    details['pads'][pad.name]['caps'] = caps.get_structure(0).to_string()

            if pad.is_linked():
                peer = pad.get_peer()
                details['pads'][pad.name]['peer'] = {
                    'pad_name': peer.name
                }
                parent = peer.get_parent_element()
                if parent:
                    details['pads'][pad.name]['peer']['element_name'] = peer.get_parent_element().name

        pad_iterator = element.iterate_pads()
        pad_iterator.foreach(handle_pad)
        elements.append(details)

        if show_inside_bin_elements and hasattr(element, 'iterate_elements'):
            iterator = element.iterate_elements()
            iterator.foreach(handle_each_element, element)

    iterator = pipeline.iterate_elements()
    iterator.foreach(handle_each_element)

    return {
        'elements': elements,
        'state': pipeline.get_state(0).state.value_nick.upper()
    }


def run_on_master_thread_when_idle(func, **func_args):
    '''
    This function allows other threads (runing the API) to call a function
    on the master thread (running GStreamer) at a moment when it is idle.
    '''
    def function_runner(args):
        if args['func'] is None:
            raise RuntimeError('Missing function to run on master thread (within run function)!')

        try:
            f = args['func']
            func_args = args['func_args']
            f(**func_args)
        except Exception as e:
            print('------------ UNCAUGHT EXCEPTION ON MASTER THREAD: %s ------------' % e)

        return False

    if func is None:
        raise RuntimeError('Missing function to run on master thread!')
    GLib.idle_add(function_runner, {'func': func, 'func_args': func_args})


def unblock_pad(block, name):
    if hasattr(block, name):
        if name in block.probes:
            getattr(block, name).remove_probe(block.probes[name])
            block.probes.pop(name)
            block.logger.debug('Removed block from %s' % name)
        # else it wasn't blocked, no need to worry
    # else it does not exist, e.g. audio in a video-only situation, so ignore


def block_pad(block, name):
    if hasattr(block, name):
        if name in block.probes:
            block.logger.warning('Attempting to block %s but already blocked' % name)
        else:
            block.probes[name] = getattr(block, name).add_probe(
                Gst.PadProbeType.BLOCK_DOWNSTREAM, _blocked_probe_callback, block)
    else:
        block.logger.error('Attempting to block pad %s that does not exist' % name)


def _blocked_probe_callback(self, _, block):
    block.logger.debug('_blocked_probe_callback called (default version)')
    return Gst.PadProbeReturn.OK
