import time, pytest, inspect
from utils import *
from PIL import Image

def test_text_overlay_element_connects_successfully(run_brave):
    '''
    Confirms that the 'text' overlay creates a 'textoverlay' element and that it connects successfully.
    '''
    run_brave()

    elements_before_adding_overlay = get_mixer_elements(1)

    add_overlay({'type': 'text', 'source': 'mixer1', 'text': 'Overlay #1', 'visible': False})
    assert_overlays([{'id': 1, 'source': 'mixer1', 'visible': False}])

    check_mixer_elements_contain_one_textoverlay(elements_before_adding_overlay, is_connected=False)

    # Now make visible and it will be connected
    update_overlay(1, {'visible': True})
    check_mixer_elements_contain_one_textoverlay(elements_before_adding_overlay, is_connected=True)

    # Now make invisible and it will not be connected
    update_overlay(1, {'visible': False})
    check_mixer_elements_contain_one_textoverlay(elements_before_adding_overlay, is_connected=False)

    # Now make active then move to another mixer... the first mixer should go down to not having that
    update_overlay(1, {'visible': True})
    add_mixer({})
    update_overlay(1, {'source': 'mixer2'})
    elements_after_moving_overlay = get_mixer_elements(1)
    assert len(elements_after_moving_overlay) == len(elements_before_adding_overlay)

    # But mixer2 will have the extra 'textoverlay' successfully
    check_mixer_elements_contain_one_textoverlay(elements_before_adding_overlay, is_connected=True, mixer_id=2)


def check_pads_peer(element, expect_a_peer):
    assert ('peer' in element['pads']['video_sink']) is expect_a_peer
    assert ('peer' in element['pads']['src']) is expect_a_peer

def get_mixer_elements(mixer_id):
    response = api_get('/api/elements')
    assert response.status_code == 200
    json_response = response.json()
    return json_response['mixers'][str(mixer_id)]['elements']

def check_mixer_elements_contain_one_textoverlay(elements_before_adding_overlay, is_connected=False, mixer_id=1):
    elements = get_mixer_elements(mixer_id)

    # 'textoverlay' should be the only additional element
    assert len(elements_before_adding_overlay) == len(elements) - 1
    textoverlay_elements = [x for x in elements if x['type'] == 'textoverlay']
    assert len(textoverlay_elements) == 1

    # The textoverlay element will not be connected
    check_pads_peer(textoverlay_elements[0], is_connected)
