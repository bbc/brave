import brave.helpers
logger = brave.helpers.get_logger('brave.rest_api')
import sanic
import sanic.response
from brave.helpers import state_string_to_constant, run_on_master_thread_when_idle
from brave.outputs.image import ImageOutput


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
    if id not in request['session'].inputs:
        return _user_error_response('No such input ID')
    request['session'].inputs[id].delete()
    return _status_ok_response()


async def delete_output(request, id):
    if id not in request['session'].outputs:
        return _user_error_response('No such output ID')
    run_on_master_thread_when_idle(request['session'].outputs[id].delete)
    return _status_ok_response()


async def delete_overlay(request, id):
    if id not in request['session'].overlays:
        return _user_error_response('No such overlay ID')
    request['session'].overlays[id].delete()
    return _status_ok_response()


async def delete_mixer(request, id):
    if id not in request['session'].mixers:
        return _user_error_response('No such mixer ID')
    request['session'].mixers[id].delete()
    return _status_ok_response()


async def cut_to_source(request, id):
    if id not in request['session'].mixers or request['session'].mixers[id] is None:
        return _user_error_response('No such mixer ID')
    if not request.json:
        return _user_error_response('Invalid JSON')
    if 'type' not in request.json or 'id' not in request.json:
        return _user_error_response("Requires 'type' and 'id' fields in JSON body")
    if request.json['type'] != 'input':
        return _user_error_response('Only inputs can be added to a mixer')

    input_id = request.json['id']
    if input_id not in request['session'].inputs or request['session'].inputs[input_id] is None:
        return _user_error_response('No such input ID')

    mixer = request['session'].mixers[id]
    connection = mixer.connection_for_src(request['session'].inputs[input_id], create_if_not_made=True)

    run_on_master_thread_when_idle(connection.cut)
    return _status_ok_response()


async def overlay_source(request, id):
    if id not in request['session'].mixers or request['session'].mixers[id] is None:
        return _user_error_response('No such mixer ID')
    if not request.json:
        return _user_error_response('Invalid JSON')
    if 'uid' not in request.json:
        return _user_error_response("Requires 'uid' field in JSON body")

    block = request['session'].uid_to_block(request.json['uid'])
    if block is None:
        return _user_error_response('No such item "%s"' % request.json['uid'])

    mixer = request['session'].mixers[id]
    connection = mixer.connection_for_src(block, create_if_not_made=True)

    run_on_master_thread_when_idle(connection.add_to_mix)
    return _status_ok_response()


async def remove_source(request, id):
    if id not in request['session'].mixers or request['session'].mixers[id] is None:
        return _user_error_response('No such mixer ID')
    if not request.json:
        return _user_error_response('Invalid JSON')
    if 'uid' not in request.json:
        return _user_error_response("Requires 'uid' field in JSON body")

    block = request['session'].uid_to_block(request.json['uid'])
    if block is None:
        return _user_error_response('No such item "%s"' % request.json['uid'])

    mixer = request['session'].mixers[id]
    connection = mixer.connection_for_src(block)
    if not connection:
        return _user_error_response('Not a source of mixer')

    run_on_master_thread_when_idle(connection.remove_from_mix)
    return _status_ok_response()


async def update_input(request, id):
    if id not in request['session'].inputs or request['session'].inputs[id] is None:
        return _user_error_response('No such input ID')

    if 'state' in request.json:
        request.json['state'] = state_string_to_constant(request.json['state'])
        if not request.json['state']:
            return _user_error_response('Invalid state')
    request['session'].inputs[id].update(request.json)
    return _status_ok_response()


async def update_output(request, id):
    if id not in request['session'].outputs or request['session'].outputs[id] is None:
        return _user_error_response('no such output id')
    if 'state' in request.json:
        request.json['state'] = state_string_to_constant(request.json['state'])
        if not request.json['state']:
            return _user_error_response('Invalid state')
    request['session'].outputs[id].update(request.json)
    return _status_ok_response()


async def update_overlay(request, id):
    if id not in request['session'].overlays or request['session'].overlays[id] is None:
        return _user_error_response('No such overlay ID')
    if 'state' in request.json:
        request.json['state'] = state_string_to_constant(request.json['state'])
        if not request.json['state']:
            return _user_error_response('Invalid state')
    request['session'].overlays[id].update(request.json)
    return _status_ok_response()


async def update_mixer(request, id):
    if id not in request['session'].mixers or request['session'].mixers[id] is None:
        return _user_error_response('No such mixer ID')
    if 'state' in request.json:
        request.json['state'] = state_string_to_constant(request.json['state'])
        if not request.json['state']:
            return _user_error_response('Invalid state')
    request['session'].mixers[id].update(request.json)
    return _status_ok_response()


async def create_input(request):
    input = request['session'].inputs.add(**request.json)
    input.setup()
    # When an input is created, which mixers should it be added to?
    # For now, it's added to the first mixer.
    # TODO find a better way
    # mixer = request['session'].mixers[0]
    # connection = mixer.connection_for_src(input, create_if_not_made=True)
    # run_on_master_thread_when_idle(connection.add_to_mix)
    logger.info('Created input #%d with details %s' % (input.id, request.json))
    return sanic.response.json({'id': input.id})


async def create_output(request):
    output = request['session'].outputs.add(**request.json)
    logger.info('Created output #%d with details %s' % (output.id, request.json))
    return sanic.response.json({'id': output.id})


async def create_overlay(request):
    overlay = request['session'].overlays.add(**request.json)
    logger.info('Created overlay #%d with details %s' % (overlay.id, request.json))
    return _status_ok_response()


async def create_mixer(request):
    mixer = request['session'].mixers.add(**request.json)
    logger.info('Created mixer #%d with details %s' % (mixer.id, request.json))
    return sanic.response.json({'id': mixer.id})


async def get_body(request, id):
    '''
    Returns the body (image contents) of a JPEG output
    '''
    if id not in request['session'].outputs or request['session'].outputs[id] is None:
        return _user_error_response('no such output id')
    output = request['session'].outputs[id]
    if type(output) != ImageOutput:
        return _user_error_response('Output is not an image')

    try:
        return await sanic.response.file_stream(
            output.props['location'],
            headers={'Cache-Control': 'max-age=1'}
        )
    except FileNotFoundError:
        return _user_error_response('No such body')


async def restart(request):
    run_on_master_thread_when_idle(request['session'].end, restart=True)
    return _status_ok_response()


def _status_ok_response():
    return sanic.response.json({'status': 'OK'})


def _user_error_response(e):
    return sanic.response.json({'error': str(e)}, 400)


def _invalid_configuration_response(e):
    logger.info('Invalid configuration from user: ' + str(e))
    return _user_error_response(e)


def internal_error_response(e):
    pretty = 'Internal error' if e is None else e
    return sanic.response.json({'error': pretty}, 500)
