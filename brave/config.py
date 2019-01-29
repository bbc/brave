import yaml
import os
import brave.exceptions
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

    _validate()


def raw():
    return {**c}


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


def inputs():
    if 'inputs' in c and c['inputs'] is not None:
        return c['inputs']
    else:
        return []


def outputs():
    if 'outputs' in c and c['outputs'] is not None:
        return c['outputs']
    else:
        return []


def overlays():
    if 'overlays' in c and c['overlays'] is not None:
        return c['overlays']
    else:
        return []


def mixers():
    return c['mixers'] if ('mixers' in c and c['mixers'] is not None) else []


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


def _validate():
    for type in ['inputs', 'outputs', 'overlays', 'mixers']:
        if type in c and c[type] is not None:
            if not isinstance(c[type], list):
                raise brave.exceptions.InvalidConfiguration(
                    'Config entry "%s" must be an array (list). It is currently: %s' % (type, c[type]))
            for entry in c[type]:
                if not isinstance(entry, dict):
                    raise brave.exceptions.InvalidConfiguration(
                        'Config entry "%s" contains an entry that is not a dictionary: %s' % (type, c[type]))
                for key, value in entry.items():
                    if not isinstance(key, str):
                        raise brave.exceptions.InvalidConfiguration(
                            'Config entry "%s" contains an entry with key "%s" that is not a string' % (type, key))
