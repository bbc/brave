'''
We test both TCP as an input and output by connecting two Braves together.
'''
import time
import utils
from utils import run_brave, create_config_file

BRAVE_1_PORT = 12345
BRAVE_2_PORT = 12346
TCP_HOST = '0.0.0.0'
TCP_PORT = 13100


def test_tcp_with_mpeg_container(run_brave, create_config_file):
    _test_tcp(run_brave, create_config_file, 'mpeg', {'enable_video': True, 'enable_audio': True})


def test_tcp_with_mpeg_container_video_only(run_brave, create_config_file):
    _test_tcp(run_brave, create_config_file, 'mpeg', {'enable_video': True, 'enable_audio': False})


def test_tcp_with_mpeg_container_audio_only(run_brave, create_config_file):
    _test_tcp(run_brave, create_config_file, 'mpeg', {'enable_video': False, 'enable_audio': True})


def test_tcp_with_ogg_container(run_brave, create_config_file):
    _test_tcp(run_brave, create_config_file, 'ogg', {'enable_video': True, 'enable_audio': True})


# Could test OGG with just video/audio but there's probably no need.

def _test_tcp(run_brave, create_config_file, container, config):
    subtest_start_brave_with_tcp_output(run_brave, create_config_file, container, {**config})
    subtest_start_brave_with_tcp_input(run_brave, create_config_file, container, {**config})

    if config['enable_video']:
        time.sleep(3)
        subtest_ensure_first_brave_content_appears_in_second()


def subtest_start_brave_with_tcp_output(run_brave, create_config_file, container, config):

    if config['enable_video']:
        config['inputs'] = [
            {
                'type': 'test_video',
                'pattern': 4,  # RED
            }
        ]
    else:
        config['inputs'] = [
            {
                'type': 'test_audio'
            }
        ]

    config['outputs'] = [
        {
            'type': 'tcp',
            'container': container,
            'source': 'input1',
            'host': TCP_HOST,
            'port': TCP_PORT
        }
    ]

    config_file = create_config_file(config)
    run_brave(config_file.name, BRAVE_1_PORT)
    time.sleep(2)
    utils.check_brave_is_running()
    utils.assert_everything_in_playing_state(port=BRAVE_1_PORT)


def subtest_start_brave_with_tcp_input(run_brave, create_config_file, container, config):
    config['inputs'] = [
        {
            'type': 'tcp_client',
            'container': container,
            'host': TCP_HOST,
            'port': TCP_PORT
        }
    ]

    if config['enable_video']:
        config['outputs'] = [
            {
                'type': 'image',
                'source': 'input1'
            },
            # PREVIEW for debugging:
            # {
            #     'type': 'local',
            #     'source': 'input1'
            # }
        ]

    config_file = create_config_file(config)
    run_brave(config_file.name, BRAVE_2_PORT)
    utils.check_brave_is_running()
    time.sleep(3)
    utils.assert_everything_in_playing_state(port=BRAVE_2_PORT)


def subtest_ensure_first_brave_content_appears_in_second():
    # First brave is all red. So second Brave should be red too.
    utils.assert_image_output_color(1, [255, 0, 0], port=BRAVE_2_PORT)

    # Now make first Brave all green
    utils.update_input(1, {'pattern': 5}, port=BRAVE_1_PORT)  # Pattern 5 is green

    # Second brave will now be green, if TCP connection is working
    time.sleep(6)
    utils.assert_image_output_color(1, [0, 255, 0], port=BRAVE_2_PORT)
