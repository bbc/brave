import time, pytest, inspect
from utils import *
from PIL import Image

def test_can_create_video_file_output(run_brave, create_config_file):
    output_video_location = create_output_video_location()

    config = {
    'default_inputs': [
        {'type': 'test_video', 'props': {'pattern': 4, 'zorder': 2}}, # pattern 4 is red
    ],
    'default_outputs': [
        {'type': 'file', 'props': { 'location': output_video_location } }
        # ,{'type': 'local'} # good for debugging
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(4)
    check_brave_is_running()
    response = api_get('/api/all')
    assert response.status_code == 200
    assert_everything_in_playing_state(response.json())
    stop_output(0)
    assert os.path.exists(output_video_location)


def test_valid_output_file():
    assert_valid_output_file(get_output_video_location())


def stop_output(num):
    path = '/api/outputs/%d' % num
    response = api_post(path, {'state': 'READY'})
    assert response.status_code == 200, 'Status code for %s was %d' % (path, response.status_code)

def assert_valid_output_file(output_video_location):
    '''
    Given a file, validates it is a video (mp4) file
    '''
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst, GLib

    Gst.init(None)
    mainloop = GLib.MainLoop()

    pipeline = Gst.ElementFactory.make("playbin")
    pipeline.set_property('uri','file://'+output_video_location)
    pipeline.set_state(Gst.State.PAUSED)

    def after_a_second():
        assert pipeline.get_state(0).state == Gst.State.PAUSED
        element = pipeline.get_by_name('inputselector1')
        caps = element.get_static_pad('src').get_current_caps()
        assert caps.to_string() == 'audio/x-raw, format=(string)F32LE, layout=(string)interleaved, rate=(int)48000, channels=(int)2, channel-mask=(bitmask)0x0000000000000003'

        element = pipeline.get_by_name('inputselector0')
        caps = element.get_static_pad('src').get_current_caps()
        assert caps.to_string() == 'video/x-raw, format=(string)Y444, width=(int)640, height=(int)360, interlace-mode=(string)progressive, multiview-mode=(string)mono, multiview-flags=(GstVideoMultiviewFlagsSet)0:ffffffff:/right-view-first/left-flipped/left-flopped/right-flipped/right-flopped/half-aspect/mixed-mono, pixel-aspect-ratio=(fraction)1/1, chroma-site=(string)mpeg2, colorimetry=(string)bt601, framerate=(fraction)30/1'

        pipeline.set_state(Gst.State.NULL)
        mainloop.quit()

    GLib.timeout_add(1000, after_a_second)
    mainloop.run()
