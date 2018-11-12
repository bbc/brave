import time, pytest, inspect
from utils import *
from PIL import Image

'''
Some core API testing
'''

def test_404(run_brave):
    run_brave()
    response = api_get('/api/overlays')
    assert response.status_code == 200
    response = api_get('/api/bad-api-path')
    assert response.status_code == 404
    assert response.json()['error'] == 'Not found'


def test_bad_body(run_brave):
    run_brave()
    response = api_post('/api/overlays', 'This is not a JSON object')
    assert response.status_code == 400
    assert response.json()['error'] == 'Invalid JSON'


def test_missing_type(run_brave):
    run_brave()
    response = api_post('/api/mixers', {})
    # assert response.status_code == 400
    assert response.json()['error'] == 'Invalid JSON not!'
