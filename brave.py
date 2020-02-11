#!/usr/bin/env python3
'''
Runs Brave as a daemon with RestAPI interface
'''

# "r_frame_rate":"47/1" trying to track down the issue with the stuttering

import sys
import threading
import signal
import argparse
import brave.session
from gi.repository import Gst
assert sys.version_info >= (3, 6)
import brave.api
import brave.config
from brave.helpers import run_on_master_thread_when_idle
import brave.exceptions


import setproctitle
setproctitle.setproctitle('brave')

def setup_args():
    parser = argparse.ArgumentParser(description='Basic Remote AV Editor')
    parser.add_argument('-c', nargs=1, metavar='<CONFIG FILE>',
                        help='path to config file')
    return vars(parser.parse_args())


def setup_config(args):
    if ('c' in args and args['c'] is not None):
        brave.config.init(args['c'][0])
    else:
        brave.config.init()


def check_gstreamer_plugins():
    needed = ['opus', 'vpx', 'nice', 'webrtc', 'dtls', 'x264', 'srtp',
              'multifile', 'tcp', 'rtmp', 'rtpmanager', 'videotestsrc', 'audiotestsrc']
    missing = list(filter(lambda p: Gst.Registry.get().find_plugin(p) is None, needed))
    if len(missing):
        print('Missing gstreamer plugins:', missing)
        return False
    return True


def start_brave():
    session = brave.session.init()

    def start_rest_api_in_separate_thread():
        try:
            brave.api.RestApi(session)
        except Exception as e:
            print('Cannot start Rest API:', e)
            run_on_master_thread_when_idle(session.end)

    threading.Thread(target=start_rest_api_in_separate_thread, name='api-thread', daemon=True).start()

    def keyboard_exit(signal, frame):
        print("Received keyboard interrupt to exit, so tidying up...")
        session.end()

    signal.signal(signal.SIGINT, keyboard_exit)
    session.start()


if __name__ == '__main__':
    Gst.init(None)
    if not check_gstreamer_plugins():
        sys.exit(1)
    args = setup_args()
    try:
        setup_config(args)
        start_brave()
    except brave.exceptions.InvalidConfiguration as e:
        print('Invalid configuration: %s' % e)
        sys.exit(1)
    except brave.exceptions.PipelineFailure as e:
        print('Failed to create GStreamer pipeline: %s' % e)
        sys.exit(1)
