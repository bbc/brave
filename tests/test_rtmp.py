import time
import os
import utils
from utils import run_brave, create_config_file

BRAVE_1_PORT = 12345
BRAVE_2_PORT = 12346


def test_rtmp(run_brave, create_config_file):
    '''
    We test both RTMP as an input and output by sending an RTMP stream from one Brave to another.
    An RTMP server is required in the middle, which needs to be provided seprately.
    Set as the RTMP_SERVER env variable, e.g.
    export RTMP_SERVER="myserver.com:10000"
    '''
    if 'RTMP_SERVER' not in os.environ:
        pytest.skip('RMTP_SERVER environment variable not set')
        return

    rtmp_url = 'rtmp://' + os.environ['RTMP_SERVER'] + '/live/test1'

    subtest_start_brave_with_rtmp_output(run_brave, create_config_file, rtmp_url)
    subtest_start_brave_with_rtmp_input(run_brave, create_config_file, rtmp_url)

    attempts_remaining = 20
    everthing_in_playing_state = False
    while attempts_remaining > 0:
        attempts_remaining -= 1
        time.sleep(1)
        everything_in_playing_state = is_brave_in_playing_state(BRAVE_1_PORT) and is_brave_in_playing_state(BRAVE_2_PORT)

    assert everything_in_playing_state, 'Cannot get everything into PLAYING state'

    # Becaue Brave 1 is showing all red, and Brave 2 is receiving Brave 1 via RTMP,
    # Then the output of Brave 2 should be all Red
    print('NOW RED')
    time.sleep(20)
    utils.assert_image_output_color(1, [255, 0, 0], port=BRAVE_2_PORT)

    # Now make first Brave all blue
    utils.update_input(1, {'pattern': 6}, port=BRAVE_1_PORT)  # Pattern 6 is blue

    # Second brave will now be blue, if TCP connection is working
    print('NOW BLUE')
    time.sleep(20) # Takes an annoyingly long time to buffer....
    utils.assert_image_output_color(1, [0, 0, 255], port=BRAVE_2_PORT)


def subtest_start_brave_with_rtmp_output(run_brave, create_config_file, rtmp_url):
    config = {
        'inputs': [
            {
                'type': 'test_video',
                'pattern': 4,  # RED
            }
        ],
        'outputs': [
            {
                'type': 'rtmp',
                'source': 'input1',
                'uri': rtmp_url
            }
        ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name, BRAVE_1_PORT)
    utils.check_brave_is_running()
    # time.sleep(0.5)


def subtest_start_brave_with_rtmp_input(run_brave, create_config_file, rtmp_url):
    config = {
        'inputs': [
            {
                'type': 'uri',
                'uri': rtmp_url
            }
        ],
        # 'mixers': [
        #     {
        #         'sources': [
        #             {'uid': 'input1'}
        #         ]
        #     }
        # ],
        'outputs': [
            {
                'type': 'image',
                'source': 'input1'
            # ADD A PREVIEW, for debugging:
            },
            {
                'type': 'local',
                'source': 'input1'
            }
        ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name, BRAVE_2_PORT)
    utils.check_brave_is_running()
    # time.sleep(0.5)


def is_brave_in_playing_state(port):
    response = utils.api_get('/api/all', port=port)
    assert response.status_code == 200
    response_json = response.json()
    return response_json['inputs'][0]['state'] == 'PLAYING' and response_json['outputs'][0]['state'] == 'PLAYING'
