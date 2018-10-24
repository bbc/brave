import logging
logger = logging.getLogger('brave.rest_api')
import sanic
import brave.session
import sanic.response
from brave.helpers import state_string_to_constant, run_on_master_thread_when_idle


async def all(request):
    session = brave.session.get_session()
    return sanic.response.json({
        'inputs': session.inputs.summarise(),
        'overlays': session.overlays.summarise(),
        'outputs': session.outputs.summarise(),
        'mixers': session.mixers.summarise()
    })


async def inputs(request):
    session = brave.session.get_session()
    return sanic.response.json(session.inputs.summarise())


async def outputs(request):
    session = brave.session.get_session()
    return sanic.response.json(session.outputs.summarise())


async def overlays(request):
    session = brave.session.get_session()
    return sanic.response.json(session.overlays.summarise())


async def mixers(request):
    session = brave.session.get_session()
    return sanic.response.json(session.mixers.summarise())


async def elements(request):
    session = brave.session.get_session()
    return sanic.response.json({
        'inputs': session.inputs.get_pipeline_details(),
        'overlays': session.overlays.get_pipeline_details(),
        'outputs': session.outputs.get_pipeline_details(),
        'mixers': session.mixers.get_pipeline_details()
    })


async def delete_input(request, id):
    session = brave.session.get_session()
    if id not in session.inputs:
        return _user_error_response('No such input ID')
    session.inputs[id].delete()
    return _status_ok_response()


async def delete_output(request, id):
    session = brave.session.get_session()
    if id not in session.outputs:
        return _user_error_response('No such output ID')
    run_on_master_thread_when_idle(session.outputs[id].delete)
    return _status_ok_response()


async def delete_overlay(request, id):
    session = brave.session.get_session()
    if id not in session.overlays:
        return _user_error_response('No such overlay ID')
    session.overlays[id].delete()
    return _status_ok_response()


async def cut_to_source(request, id):
    session = brave.session.get_session()
    if id not in session.mixers or session.mixers[id] is None:
        return _user_error_response('No such mixer ID')
    if not request.json:
        return _user_error_response('Invalid JSON')
    if 'type' not in request.json or 'id' not in request.json:
        return _user_error_response("Requires 'type' and 'id' fields in JSON body")
    if request.json['type'] != 'input':
        return _user_error_response('Only inputs can be added to a mixer')

    input_id = request.json['id']
    if input_id not in session.inputs or session.inputs[input_id] is None:
        return _user_error_response('No such input ID')

    run_on_master_thread_when_idle(session.mixers[id].cut_to_source,
                                   source_to_switch_to=session.inputs[input_id])
    return _status_ok_response()


async def overlay_source(request, id):
    session = brave.session.get_session()
    if id not in session.mixers or session.mixers[id] is None:
        return _user_error_response('No such mixer ID')
    if not request.json:
        return _user_error_response('Invalid JSON')
    if 'type' not in request.json or 'id' not in request.json:
        return _user_error_response("Requires 'type' and 'id' fields in JSON body")
    if request.json['type'] != 'input':
        return _user_error_response('Only inputs can be added to a mixer')

    input_id = request.json['id']
    if input_id not in session.inputs or session.inputs[input_id] is None:
        return _user_error_response('No such input ID')
    run_on_master_thread_when_idle(session.inputs[input_id].add_to_mix)
    return _status_ok_response()


async def remove_source(request, id):
    session = brave.session.get_session()
    if id not in session.mixers or session.mixers[id] is None:
        return _user_error_response('No such mixer ID')
    if not request.json:
        return _user_error_response('Invalid JSON')
    if 'type' not in request.json or 'id' not in request.json:
        return _user_error_response("Requires 'type' and 'id' fields in JSON body")
    if request.json['type'] != 'input':
        return _user_error_response('Only inputs can be added to a mixer')

    input_id = request.json['id']
    if input_id not in session.inputs or session.inputs[input_id] is None:
        return _user_error_response('No such inputop ID')
    run_on_master_thread_when_idle(session.inputs[input_id].remove_from_mix)
    return _status_ok_response()


async def update_input(request, id):
    session = brave.session.get_session()
    if not request.json:
        return _invalid_json_response()
    if id not in session.inputs or session.inputs[id] is None:
        return _user_error_response('No such input ID')

    if 'state' in request.json:
        request.json['state'] = state_string_to_constant(request.json['state'])
        if not request.json['state']:
            return _user_error_response('Invalid state')
    try:
        session.inputs[id].update(request.json)
    except brave.exceptions.InvalidConfiguration as e:
        return _invalid_configuration_response(e)
    return _status_ok_response()


async def update_output(request, id):
    session = brave.session.get_session()
    if not request.json:
        return _user_error_response('Not valid JSON')
    if id not in session.outputs or session.outputs[id] is None:
        return _user_error_response('no such output id')
    if 'state' in request.json:
        request.json['state'] = state_string_to_constant(request.json['state'])
        if not request.json['state']:
            return _user_error_response('Invalid state')
    session.outputs[id].update(request.json)
    return _status_ok_response()


async def update_overlay(request, id):
    session = brave.session.get_session()
    if not request.json:
        return _invalid_json_response('Not valid JSON')
    if id not in session.overlays or session.overlays[id] is None:
        return _user_error_response('No such overlay ID')
    if 'state' in request.json:
        request.json['state'] = state_string_to_constant(request.json['state'])
        if not request.json['state']:
            return _user_error_response('Invalid state')
    try:
        session.overlays[id].update(request.json)
    except brave.exceptions.InvalidConfiguration as e:
        return _invalid_configuration_response(e)
    return _status_ok_response()


async def update_mixer(request, id):
    session = brave.session.get_session()
    if not request.json:
        return _invalid_json_response()
    if id not in session.mixers or session.mixers[id] is None:
        return _user_error_response('No such mixer ID')
    if 'state' in request.json:
        request.json['state'] = state_string_to_constant(request.json['state'])
        if not request.json['state']:
            return _user_error_response('Invalid state')
    try:
        session.mixers[id].update(request.json)
    except brave.exceptions.InvalidConfiguration as e:
        return _invalid_configuration_response(e)
    return _status_ok_response()


async def create_input(request):
    session = brave.session.get_session()
    if not request.json:
        return _invalid_json_response()
    try:
        input = session.inputs.add(**request.json)
        run_on_master_thread_when_idle(input.add_to_mix)
    except brave.exceptions.InvalidConfiguration as e:
        return _invalid_configuration_response(e)
    return _status_ok_response()


async def create_output(request):
    session = brave.session.get_session()
    if not request.json:
        return _invalid_json_response()
    try:
        output = session.outputs.add(**request.json)
        output.link_from_source()
    except brave.exceptions.InvalidConfiguration as e:
        return _invalid_configuration_response(e)
    logger.info('Created output #' + str(output.id) + ' with details ' + str(request.json))
    return sanic.response.json({'status': 'OK', 'id': output.id})


async def create_overlay(request):
    session = brave.session.get_session()
    if not request.json:
        return _invalid_json_response()
    try:
        overlay = session.overlays.add(**request.json, mixer=session.mixers[0])
    except brave.exceptions.InvalidConfiguration as e:
        return _invalid_configuration_response(e)
    session.overlays.ensure_overlays_are_correctly_connected()
    logger.info('Created overlay #' + str(overlay.id) + ' with details ' + str(request.json))
    return _status_ok_response()


async def restart(request):
    run_on_master_thread_when_idle(brave.session.get_session().end, restart=True)
    return _status_ok_response()


def _status_ok_response():
    return sanic.response.json({'status': 'OK'})


def _user_error_response(e):
    return sanic.response.json({'error': str(e)}, 400)


def _invalid_json_response():
    return _user_error_response('Invalid JSON')


def _invalid_configuration_response(e):
    logger.info('Invalid configuration from user: ' + str(e))
    return _user_error_response(e)


def internal_error_response(e):
    pretty = 'Internal error' if e is None else e
    return sanic.response.json({'error': pretty}, 500)
