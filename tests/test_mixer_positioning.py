import time, pytest, inspect
import utils
from utils import run_brave, create_config_file
from PIL import Image

'''
Does the mixer correctly position inputs, so that we can do picture-in-picture or a video-wall?
'''

def test_mixer_positioning(run_brave, create_config_file):
    subtest_start_brave_with_multiple_positioned_inputs(run_brave, create_config_file)
    subtest_move_input3_right()
    subtest_cut_with_position_and_size()
    subtest_cut_by_setting_source_property()

def subtest_start_brave_with_multiple_positioned_inputs(run_brave, create_config_file):
    config = {
        'inputs': [
            {'type': 'test_video', 'pattern': 3}, # white
            {'type': 'test_video', 'pattern': 4}, # red
            {'type': 'test_video', 'pattern': 5}, # green
            {'type': 'test_video', 'pattern': 6}, # blue
        ],
        'mixers': [
            {'width': 160, 'height': 90, 'pattern': 2, 'sources': [
                { 'uid': 'input1', 'zorder': 1 },
                { 'uid': 'input2', 'zorder': 2, 'width': 80 },
                { 'uid': 'input3', 'zorder': 3, 'width': 80, 'height': 45 },
                { 'uid': 'input4', 'zorder': 4, 'xpos': 80, 'ypos': 45 }
            ]}
        ],
        'outputs': [{'type': 'image', 'width': 160, 'height': 90}]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    utils.check_brave_is_running()
    time.sleep(4)
    utils.assert_everything_in_playing_state()
    utils.assert_mixers([{
        'id': 1,
        'sources': [
            {'uid': 'input1', 'in_mix': True, 'zorder': 1},
            {'uid': 'input2', 'in_mix': True, 'zorder': 2, 'width': 80},
            {'uid': 'input3', 'in_mix': True, 'zorder': 3, 'width': 80, 'height': 45},
            {'uid': 'input4', 'in_mix': True, 'zorder': 4, 'xpos': 80, 'ypos': 45}
        ]
    }])

    im = utils.get_raw_image_for_output(1)
    utils.assert_image_color_at_dimension(im, (10,10), (0, 255, 0))
    utils.assert_image_color_at_dimension(im, (150,10), (255, 255, 255))
    utils.assert_image_color_at_dimension(im, (10, 80), (255, 0, 0))
    utils.assert_image_color_at_dimension(im, (150,80), (0, 0, 255))


def subtest_move_input3_right():
    utils.overlay_source('input3', 1, details={'xpos': 80})
    utils.assert_mixers([{
        'id': 1,
        'sources': [
            {'uid': 'input1', 'in_mix': True, 'zorder': 1},
            {'uid': 'input2', 'in_mix': True, 'zorder': 2, 'width': 80},
            {'uid': 'input3', 'in_mix': True, 'zorder': 3, 'xpos': 80, 'width': 80, 'height': 45},
            {'uid': 'input4', 'in_mix': True, 'zorder': 4, 'xpos': 80, 'ypos': 45}
        ]
    }])
    time.sleep(3)
    # Top-right now green, top-left falls back to red
    im = utils.get_raw_image_for_output(1)
    utils.assert_image_color_at_dimension(im, (10,10), (255, 0, 0))
    utils.assert_image_color_at_dimension(im, (150,10), (0, 255, 0))
    utils.assert_image_color_at_dimension(im, (10, 80), (255, 0, 0))
    utils.assert_image_color_at_dimension(im, (150,80), (0, 0, 255))


def subtest_cut_with_position_and_size():
    # 'Cut' rather than 'overlay' will remove all other sources
    # 'width' and 'height' are bigger than the mixer
    # xpos not being set, so should retain the value from earlier.
    utils.cut_to_source('input4', 1, details={'ypos': 0, 'width': 300, 'height': 300})
    time.sleep(0.5)
    utils.assert_mixers([{
        'id': 1,
        'sources': [
            {'uid': 'input1', 'in_mix': False, 'zorder': 1},
            {'uid': 'input2', 'in_mix': False, 'zorder': 2, 'width': 80},
            {'uid': 'input3', 'in_mix': False, 'zorder': 3, 'xpos': 80, 'width': 80, 'height': 45},
            {'uid': 'input4', 'in_mix': True, 'zorder': 4, 'xpos': 80, 'ypos': 0, 'width': 300, 'height': 300}
        ]
    }])

    time.sleep(3)
    # Right-hand-side blue, left-hand-side black
    im = utils.get_raw_image_for_output(1)
    utils.assert_image_color_at_dimension(im, (10,10), (0, 0, 0))
    utils.assert_image_color_at_dimension(im, (150,10), (0, 0, 255))
    utils.assert_image_color_at_dimension(im, (10, 80), (0, 0, 0))
    utils.assert_image_color_at_dimension(im, (150,80), (0, 0, 255))


def subtest_cut_by_setting_source_property():
    utils.update_mixer(1, {'sources': [
        {'uid': 'input1'},
        {'uid': 'input4', 'xpos': 0, 'height': 45}
    ]})
    time.sleep(0.5)
    utils.assert_mixers([{
        'id': 1,
        'sources': [
            {'uid': 'input1', 'in_mix': True, 'zorder': 1},
            {'uid': 'input2', 'in_mix': False, 'zorder': 2, 'width': 80},
            {'uid': 'input3', 'in_mix': False, 'zorder': 3, 'xpos': 80, 'width': 80, 'height': 45},
            {'uid': 'input4', 'in_mix': True, 'zorder': 4, 'xpos': 0, 'ypos': 0, 'width': 300, 'height': 45}
        ]
    }])

    time.sleep(3)
    # Top blue, bottom white
    im = utils.get_raw_image_for_output(1)
    utils.assert_image_color_at_dimension(im, (10,10), (0, 0, 255))
    utils.assert_image_color_at_dimension(im, (150,10), (0, 0, 255))
    utils.assert_image_color_at_dimension(im, (10, 80), (255, 255, 255))
    utils.assert_image_color_at_dimension(im, (150,80), (255, 255, 255))
