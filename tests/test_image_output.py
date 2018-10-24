import time, pytest, inspect
from utils import *
from PIL import Image


def test_image_output(run_brave, create_config_file):
    output_image_location = create_output_image_location()

    config = {
    'default_inputs': [
        {'type': 'test_video', 'props': {'pattern': 4, 'zorder': 2}}, # pattern 4 is red
    ],
    'default_outputs': [
        {'type': 'local'}, # good for debugging
        {'type': 'image', 'props': { 'location': output_image_location } }
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(4)
    check_brave_is_running()
    response = api_get('/api/all')
    assert response.status_code == 200
    assert_everything_in_playing_state(response.json())


    im = Image.open(output_image_location)
    assert im.format == 'JPEG'
    assert im.size[0] == 640
    assert im.size[1] == 360
    assert im.mode == 'RGB'
    print('format/size/node=', im.format, im.size, im.mode)
    assert_image_is_red(im, output_image_location)


def assert_image_is_red(im, output_image_location):
    # Select a few pixels to check:
    dimensions = [(0,0), (100,0), (0,100), (100,100), (im.size[0]-1, im.size[1]-1)]
    for dimension in dimensions:
        p = im.getpixel(dimension)
        print('dimension=', dimension, ', pixel=', p)
        # p is a tuple, for RGB, each between 0 and 255
        assert p[0] > 200, "Pixel " + str(dimension) + "does not look very red, check " + output_image_location
        assert p[1] < 50, "Pixel " + str(dimension) + "should be red not green, check " + output_image_location
        assert p[1] < 50, "Pixel " + str(dimension) + "should be red not blue, check " + output_image_location
