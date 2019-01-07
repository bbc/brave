import yaml
import os
DEFAULT_CONFIG_FILENAME = 'config/default.yaml'
c = {}


def init(filename=DEFAULT_CONFIG_FILENAME):
    try:
        with open(filename, 'r') as stream:
            global c
            c = yaml.load(stream)
            if c is None:
                c = {}
    except FileNotFoundError as e:
        print('Unable to open config file "%s": %s' % (filename, e))
        exit(1)


def api_host():
    if 'HOST' in os.environ:
        return os.environ['HOST']
    return c['api_host'] if 'api_host' in c else '127.0.0.1'


def api_port():
    if 'PORT' in os.environ:
        return int(os.environ['PORT'])
    return c['api_port'] if 'api_port' in c else 5000


def enable_audio():
    return 'enable_audio' not in c or c['enable_audio'] is True


def enable_video():
    return 'enable_video' not in c or c['enable_video'] is True


def default_mixer_width():
    return c['default_mixer_width'] if 'default_mixer_width' in c else 640


def default_mixer_height():
    return c['default_mixer_height'] if 'default_mixer_height' in c else 360


def default_inputs():
    if 'default_inputs' in c and c['default_inputs'] is not None:
        return c['default_inputs']
    else:
        return []


def default_outputs():
    if 'default_outputs' in c and c['default_outputs'] is not None:
        return c['default_outputs']
    else:
        return []


def default_overlays():
    if 'default_overlays' in c and c['default_overlays'] is not None:
        return c['default_overlays']
    else:
        return []


def default_mixers():
    return c['default_mixers'] if ('default_mixers' in c and c['default_mixers'] is not None) else []


def default_audio_caps():
    return 'audio/x-raw,channels=2,layout=interleaved,rate=48000,format=S16LE'


def stun_server():
    'Should be in the format <host>:<port>'
    if 'STUN_SERVER' in os.environ:
        return os.environ['STUN_SERVER']
    return c['stun_server'] if 'stun_server' in c else 'stun.l.google.com:19302'


def turn_server():
    'Should be in the format <username>:<credential>@<host>:<port>'
    if 'TURN_SERVER' in os.environ:
        return os.environ['TURN_SERVER']
    return c['turn_server'] if 'turn_server' in c else None
