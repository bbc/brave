import brave.helpers
logger = brave.helpers.get_logger('api_routes')
import sanic
import sanic.response
from brave.helpers import state_string_to_constant, run_on_master_thread_when_idle
from brave.outputs.image import ImageOutput
from sanic.exceptions import InvalidUsage


async def all(request):
    return sanic.response.json({
        'inputs': request['session'].inputs.summarise(),
        'overlays': request['session'].overlays.summarise(),
        'outputs': request['session'].outputs.summarise(),
        'mixers': request['session'].mixers.summarise()
    })


async def inputs(request):
    return sanic.response.json(request['session'].inputs.summarise())


async def outputs(request):
    return sanic.response.json(request['session'].outputs.summarise())


async def overlays(request):
    return sanic.response.json(request['session'].overlays.summarise())


async def mixers(request):
    return sanic.response.json(request['session'].mixers.summarise())


async def elements(request):
    show_inside_bin_elements = 'show_inside_bin_elements' in request.args
    return sanic.response.json({
        'inputs': request['session'].inputs.get_pipeline_details(show_inside_bin_elements),
        'overlays': request['session'].overlays.get_pipeline_details(show_inside_bin_elements),
        'outputs': request['session'].outputs.get_pipeline_details(show_inside_bin_elements),
        'mixers': request['session'].mixers.get_pipeline_details(show_inside_bin_elements)
    })


async def delete_input(request, id):
    input = _get_input(request, id)
    run_on_master_thread_when_idle(input.delete)
    return _status_ok_response()


async def delete_output(request, id):
    output = _get_output(request, id)
    run_on_master_thread_when_idle(output.delete)
    return _status_ok_response()


async def delete_overlay(request, id):
    overlay = _get_overlay(request, id)
    run_on_master_thread_when_idle(overlay.delete)
    return _status_ok_response()


async def delete_mixer(request, id):
    mixer = _get_mixer(request, id)
    run_on_master_thread_when_idle(mixer.delete)
    return _status_ok_response()


async def cut_to_source(request, id):
    connection = _get_connection(request, id, create_if_not_made=True)
    run_on_master_thread_when_idle(connection.cut)
    return _status_ok_response()


async def overlay_source(request, id):
    connection = _get_connection(request, id, create_if_not_made=True)
    run_on_master_thread_when_idle(connection.add_to_mix)
    return _status_ok_response()


async def remove_source(request, id):
    connection = _get_connection(request, id, create_if_not_made=False)
    run_on_master_thread_when_idle(connection.remove_from_mix)
    return _status_ok_response()


async def update_input(request, id):
    _validate_state(request)
    _get_input(request, id).update(request.json)
    return _status_ok_response()


async def update_output(request, id):
    _validate_state(request)
    _get_output(request, id).update(request.json)
    return _status_ok_response()


async def update_overlay(request, id):
    _validate_state(request)
    _get_overlay(request, id).update(request.json)
    return _status_ok_response()


async def update_mixer(request, id):
    _validate_state(request)
    _get_mixer(request, id).update(request.json)
    return _status_ok_response()


async def create_input(request):
    input = request['session'].inputs.add(**request.json)
    input.setup()
    logger.info('Created input #%d with details %s' % (input.id, request.json))
    return sanic.response.json({'id': input.id, 'uid': input.uid()})


async def create_output(request):
    output = request['session'].outputs.add(**request.json)
    logger.info('Created output #%d with details %s' % (output.id, request.json))
    return sanic.response.json({'id': output.id, 'uid': output.uid()})


async def create_overlay(request):
    overlay = request['session'].overlays.add(**request.json)
    logger.info('Created overlay #%d with details %s' % (overlay.id, request.json))
    return sanic.response.json({'id': overlay.id, 'uid': overlay.uid()})


async def create_mixer(request):
    mixer = request['session'].mixers.add(**request.json)
    logger.info('Created mixer #%d with details %s' % (mixer.id, request.json))
    return sanic.response.json({'id': mixer.id, 'uid': mixer.uid()})


async def get_body(request, id):
    '''
    Returns the body (image contents) of a JPEG output
    '''
    output = _get_output(request, id)
    if type(output) != ImageOutput:
        raise InvalidUsage('Output is not an image')

    try:
        return await sanic.response.file_stream(
            output.location,
            headers={'Cache-Control': 'max-age=1'}
        )
    except FileNotFoundError:
        raise InvalidUsage('No such body')


async def restart(request):
    run_on_master_thread_when_idle(request['session'].end, restart=True)
    return _status_ok_response()


def _get_output(request, id):
    if id not in request['session'].outputs or request['session'].outputs[id] is None:
        raise InvalidUsage('no such output ID')
    return request['session'].outputs[id]


def _get_input(request, id):
    if id not in request['session'].inputs or request['session'].inputs[id] is None:
        raise InvalidUsage('no such input ID')
    return request['session'].inputs[id]


def _get_overlay(request, id):
    if id not in request['session'].overlays or request['session'].overlays[id] is None:
        raise InvalidUsage('no such overlay ID')
    return request['session'].overlays[id]


def _get_mixer(request, id):
    if id not in request['session'].mixers or request['session'].mixers[id] is None:
        raise InvalidUsage('no such mixer ID')
    return request['session'].mixers[id]


def _get_connection(request, id, create_if_not_made):
    if 'source' not in request.json:
        raise InvalidUsage('Requires "source" field in JSON body')

    source = request['session'].uid_to_block(request.json['source'])
    if source is None:
        raise InvalidUsage('No such item "%s"' % request.json['source'])

    connection = _get_mixer(request, id).connection_for_source(source, create_if_not_made=create_if_not_made)
    if not connection and create_if_not_made is True:
        raise InvalidUsage('Unable to connect "%s" to mixer %d' % (request.json['source'], id))
    return connection


def _status_ok_response():
    return sanic.response.json({'status': 'OK'})


def _validate_state(request):
    if 'state' in request.json:
        request.json['state'] = state_string_to_constant(request.json['state'])
        if not request.json['state']:
            raise InvalidUsage('Invalid state. Must be PLAYING, PAUSED, READY or NULL.')
