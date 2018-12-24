import subprocess, sys, time, tempfile, yaml, os, requests, pytest, signal, json, inspect, random
from PIL import Image

brave_processes = {}

@pytest.fixture #(scope="module")
def run_brave(config_file=None, port=None):
    def _run_brave(config_file=None, port=None):
        cmd = './brave.py'
        if (config_file):
            cmd += ' -c ' + config_file
        if port:
            cmd = 'PORT=%d %s' % (port, cmd)
        global brave_processes
        brave_processes[config_file] = subprocess.Popen(cmd, shell=True)
        time.sleep(1)
    yield _run_brave
    print('Stopping Brave...')
    global brave_processes
    for config_file, process in brave_processes.items():
        process.send_signal(signal.SIGINT)
    brave_processes = {}


def api_get(path, port=5000, stream=False):
    url = 'http://localhost:%d%s' % (port, path)
    return requests.get(url, stream=stream)


def api_post(path, data):
    url = 'http://localhost:5000' + path
    return requests.post(url, data=json.dumps(data))


def api_put(path, data):
    url = 'http://localhost:5000' + path
    return requests.put(url, data=json.dumps(data))


def api_delete(path):
    url = 'http://localhost:5000' + path
    return requests.delete(url)

brave_process = None


@pytest.fixture
def create_config_file():

    created_config_files = []

    def _create_config_file(config):
        fp = tempfile.NamedTemporaryFile(delete=False)
        fp.write(yaml.dump(config).encode())
        fp.close()
        created_config_files.append(fp)
        return fp

    yield _create_config_file
    for fp in created_config_files:
        os.unlink(fp.name)


def check_brave_is_running():
    global brave_processes
    for config_file, process in brave_processes.items():
        assert process.poll() == None


def check_return_value(return_value):
    global brave_processes
    for config_file, process in brave_processes.items():
        assert process.poll() == return_value


def assert_inputs_in_playing_state(json_response):
    if 'inputs' in json_response:
        for input in json_response['inputs']:
            assert input['state'] == 'PLAYING', 'Input in %s state, not PLAYING: %s' % (input['state'], str(input))


def assert_outputs_in_playing_state(json_response):
    if 'outputs' in json_response:
        for output in json_response['outputs']:
            assert output['state'] == 'PLAYING', 'Output in %s state, not PLAYING: %s' % (output['state'], str(output))


def assert_mixers_in_playing_state(json_response):
    if 'mixers' in json_response:
        for mixer in json_response['mixers']:
            assert mixer['state'] == 'PLAYING', 'Mixer in %s state, not PLAYING: %s' % (mixer['state'], str(mixer))


def assert_overlays_in_playing_state(json_response):
    if 'overlays' in json_response:
        for overlay in json_response['overlays']:
            assert overlay['state'] == 'PLAYING', 'Overlay in %s state, not PLAYING: %s' % (overlay['state'], str(overlay))


def assert_everything_in_playing_state(json_response=None):
    if json_response is None:
        json_response = api_get('/api/all')
    assert_inputs_in_playing_state(json_response)
    assert_outputs_in_playing_state(json_response)
    assert_mixers_in_playing_state(json_response)
    assert_overlays_in_playing_state(json_response)


def delete_if_exists(name):
    try:
        os.unlink(name)
    except FileNotFoundError:
        pass


def test_directory():
    return os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


temp_directory = None
def get_temp_directory():
    global temp_directory
    if not temp_directory:
        temp_directory = tempfile.TemporaryDirectory()
    return temp_directory.name


def create_output_image_location():
    img_file = get_temp_directory() + '/image' + str(random.randint(100000,200000)) + '.jpg'
    return img_file


OUTPUT_VIDEO_LOCATION = '/tmp/test.mp4'
def get_output_video_location():
    return OUTPUT_VIDEO_LOCATION


def create_output_video_location():
    global OUTPUT_VIDEO_LOCATION
    delete_if_exists(OUTPUT_VIDEO_LOCATION)
    return OUTPUT_VIDEO_LOCATION


def add_output(details, status_code=200):
    response = api_put('/api/outputs', details)
    assert response.status_code == status_code, 'Expected status code %s but got %s, body was:%s' % (status_code, response.status_code, response.json())
    time.sleep(0.5)
    return response.json()


def delete_output(id, expected_status_code=200):
    response = api_delete('/api/outputs/' + str(id))
    assert response.status_code == expected_status_code
    time.sleep(0.2)


def update_output(id, updates, expected_status_code=200):
    response = api_post('/api/outputs/' + str(id), updates)
    assert response.status_code == expected_status_code, 'Expected status code %s but got %s, body was:%s' % (expected_status_code, response.status_code, response.json())
    time.sleep(0.2)


def add_overlay(details, status_code=200):
    response = api_put('/api/overlays', details)
    assert response.status_code == status_code, 'Status code to make overlay was %d' % response.status_code


def delete_overlay(overlay_id):
    response = api_delete('/api/overlays/%d' % overlay_id)
    assert response.status_code == 200, 'Status code to delete overlay was %d' % response.status_code


def update_overlay(overlay_id, details, status_code=200):
    response = api_post('/api/overlays/' + str(overlay_id), details)
    assert response.status_code == status_code, 'Status code to update overlay was %d' % response.status_code


def set_mixer_state(mixer_id, state, status_code=200):
    response = api_post('/api/mixers/' + str(mixer_id), {'state': state})
    assert response.status_code == status_code, 'Status code to update mixer was %d' % response.status_code


def assert_outputs(outputs, check_playing_state=True):
    response = api_get('/api/all')
    assert response.status_code == 200
    if check_playing_state:
        assert_everything_in_playing_state(response.json())
    assert len(outputs) == len(response.json()['outputs'])

    # Chcek /api/outputs - should be the same
    response = api_get('/api/outputs')
    assert response.status_code == 200
    assert len(outputs) == len(response.json())

    for count, expected_output in enumerate(outputs):
        actual_output = response.json()[count]
        for (key, value) in expected_output.items():
            if key == 'props':
                for (props_key, props_value) in expected_output['props'].items():
                    assert props_key in actual_output['props']
                    assert props_value == actual_output['props'][props_key], 'For output %s, for key %s, expected %s but got %s' % (expected_output['id'], props_key, props_value, actual_output['props'][props_key])
            elif key == 'source':
                if value is None:
                    assert 'source' not in actual_output
                else:
                    assert 'source' in actual_output, 'Expected source in %s' % actual_output
                    assert actual_output['source'] == value
            else:
                assert value == actual_output[key], 'Key "%s" expected to be "%s", but was "%s"' % (key, value, actual_output[key])


def assert_mixers(mixers):
    # Check /api/all
    response = api_get('/api/all')
    assert response.status_code == 200
    assert_everything_in_playing_state(response.json())
    assert len(mixers) == len(response.json()['mixers'])

    # Check /api/mixers - should be the same
    response = api_get('/api/mixers')
    assert response.status_code == 200
    assert len(mixers) == len(response.json())

    for count, expected_mixer in enumerate(mixers):
        actual_mixer = response.json()[count]
        for (key, value) in expected_mixer.items():
            if key == 'props':
                for (props_key, props_value) in expected_mixer['props'].items():
                    assert props_key in actual_mixer['props']
                    assert props_value == actual_mixer['props'][props_key], 'For mixer %s, for key %s, expected %s but got %s' % (expected_mixer['id'], props_key, props_value, actual_mixer['props'][props_key])
            else:
                assert value == actual_mixer[key], 'Key "%s" expected to be "%s", but was "%s"' % (key, value, actual_mixer[key])


def assert_overlays(overlays):

    # Chcek /api/all
    response = api_get('/api/all')
    assert response.status_code == 200
    assert_inputs_in_playing_state(response.json())
    assert_mixers_in_playing_state(response.json())
    assert len(overlays) == len(response.json()['overlays'])

    # Chcek /api/overlays - should be the same
    response = api_get('/api/overlays')
    assert response.status_code == 200
    assert len(overlays) == len(response.json())

    for count, expected_overlay in enumerate(overlays):
        actual_overlay = response.json()[count]
        for (key, value) in expected_overlay.items():
            assert key in actual_overlay
            if key == 'props':
                for (props_key, props_value) in expected_overlay['props'].items():
                    assert props_key in actual_overlay['props']
                    assert props_value == actual_overlay['props'][props_key], 'For overlay %s, for key %s, expected %s but got %s' % (expected_overlay['id'], props_key, props_value, actual_overlay['props'][props_key])
            else:
                assert value == actual_overlay[key], 'Key "%s" expected to be "%s", but was "%s"' % (key, value, actual_overlay[key])


def add_input(details):
    response = api_put('/api/inputs', details)
    assert response.status_code == 200
    time.sleep(0.2)
    return response.json()


def delete_input(id, expected_status_code=200):
    response = api_delete('/api/inputs/' + str(id))
    assert response.status_code == expected_status_code
    time.sleep(0.2)


def update_input(id, updates, expected_status_code=200):
    response = api_post('/api/inputs/' + str(id), updates)
    assert response.status_code == expected_status_code
    time.sleep(0.2)


def add_mixer(details):
    response = api_put('/api/mixers', details)
    assert response.status_code == 200
    time.sleep(0.2)


def update_mixer(id, updates, expected_status_code=200):
    response = api_post('/api/mixers/' + str(id), updates)
    assert response.status_code == expected_status_code
    time.sleep(0.2)


def assert_inputs(inputs, check_playing_state=True):
    response = api_get('/api/all')
    assert response.status_code == 200
    if check_playing_state:
        assert_everything_in_playing_state(response.json())
    assert len(inputs) == len(response.json()['inputs'])

    # Test /api/inputs as well as /api/all:
    response = api_get('/api/inputs')
    assert response.status_code == 200
    assert len(inputs) == len(response.json())

    for count, expected_input in enumerate(inputs):
        actual_input = response.json()[count]
        for (key, value) in expected_input.items():
            assert key in actual_input
            if key == 'props':
                for (key, value) in expected_input['props'].items():
                    assert key in actual_input['props']
                    assert value == actual_input['props'][key]
            else:
                assert value == actual_input[key], 'For key "%s", expected "%s" but got "%s"' % (key, value, actual_input[key])


def delete_mixer(id, expected_status_code=200):
    response = api_delete('/api/mixers/' + str(id))
    assert response.status_code == expected_status_code
    time.sleep(0.2)


def cut_to_source(source, mixer_id, status_code=200):
    response = api_post('/api/mixers/%d/cut_to_source' % mixer_id, {'source': source})
    assert response.status_code == status_code, 'Expected status code %s but got %s, body was:%s' % (status_code, response.status_code, response.json())
    time.sleep(0.5)


def assert_image_file_color(output_image_location, expected_color):
    im = Image.open(output_image_location)
    assert_image_color(im, expected_color)


def assert_image_output_color(output_id, expected_color):
    im = Image.open(api_get('/api/outputs/%d/body' % output_id, stream = True).raw)
    assert_image_color(im, expected_color)


def assert_image_color(im, expected_color):
    assert im.format == 'JPEG'
    assert im.size == (640, 360)
    assert im.mode == 'RGB'
    __assert_image_color(im, expected_color)

def __assert_image_color(im, expected):
    '''
    Given an image and a color tuple, asserts the image is made up solely of that color.
    '''
    NAMES = ['red', 'green', 'blue']
    PERMITTED_RANGE=10

    # Select a few pixels to check:
    dimensions = [(0,0), (100,0), (0,100), (100,100), (im.size[0]-1, im.size[1]-1)]
    for dimension in dimensions:
        actual = im.getpixel(dimension)
        p = actual
        for i in range(len(expected)):
            assert (expected[i]-PERMITTED_RANGE) < actual[i] < (expected[i]+PERMITTED_RANGE), \
                '%s value was %d but expected %d (within range of %d)' % (NAMES[i], actual[i], expected[i], PERMITTED_RANGE)
