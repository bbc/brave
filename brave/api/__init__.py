import brave.helpers
import asyncio
import uvloop
logger = brave.helpers.get_logger('api')
from sanic import Sanic
import sanic.response
from sanic.exceptions import NotFound, InvalidUsage
import brave.config as config
import brave.api.websockets_handler
import brave.api.route_handler
import brave.exceptions


class RestApi(object):
    '''
    Class to provide Brave's Restful API
    '''

    def __init__(self, session):
        app = Sanic()
        app.config.KEEP_ALIVE = False
        session.rest_api = self
        self.webockets_handler = brave.api.websockets_handler.WebsocketsHandler(session)
        route_handler = brave.api.route_handler

        app.static('/', './public/index.html', name='index.html')
        app.static('/elements_table', './public/elements_table.html', name='elements_table.html')
        app.static('/style.css', './public/style.css', name='style.css')
        app.static('/js/', './public/js/')
        app.static('/css/', './public/css/')
        app.static('/output_images/', '/usr/local/share/brave/output_images/')

        @app.exception(NotFound)
        def not_found(request, exception):
            return sanic.response.json({'error': 'Not found'}, 404)

        @app.exception(InvalidUsage)
        def invalid_usage(request, exception):
            return sanic.response.json({'error': 'Invalid request: %s' % exception}, 400)

        @app.middleware('request')
        async def give_session_to_each_route_handler(request):
            request['session'] = session

        @app.middleware('request')
        async def ensure_objects_always_provided_in_json(request):
            if request.method in ['POST', 'PUT'] and not isinstance(request.json, dict):
                return sanic.response.json({'error': 'Invalid JSON'}, 400)

        @app.exception(brave.exceptions.InvalidConfiguration)
        def invalid_cf(request, exception):
            msg = 'Invalid configuration: ' + str(exception)
            logger.debug(msg)
            return sanic.response.json({'error': msg}, 400)

        @app.exception(brave.exceptions.PipelineFailure)
        def pipeline_creation_failure(request, exception):
            return sanic.response.json({'error': str(exception)}, 500)

        app.add_route(route_handler.all, "/api/all")
        app.add_route(route_handler.inputs, "/api/inputs")
        app.add_route(route_handler.outputs, "/api/outputs")
        app.add_route(route_handler.overlays, "/api/overlays")
        app.add_route(route_handler.mixers, "/api/mixers")
        app.add_route(route_handler.elements, "/api/elements")

        app.add_route(route_handler.create_input, '/api/inputs', methods=['PUT'])
        app.add_route(route_handler.create_output, '/api/outputs', methods=['PUT'])
        app.add_route(route_handler.create_overlay, '/api/overlays', methods=['PUT'])
        app.add_route(route_handler.create_mixer, '/api/mixers', methods=['PUT'])

        app.add_route(route_handler.update_input, '/api/inputs/<id:int>', methods=['POST'])
        app.add_route(route_handler.update_output, '/api/outputs/<id:int>', methods=['POST'])
        app.add_route(route_handler.update_overlay, '/api/overlays/<id:int>', methods=['POST'])
        app.add_route(route_handler.update_mixer, '/api/mixers/<id:int>', methods=['POST'])

        app.add_route(route_handler.delete_input, '/api/inputs/<id:int>', methods=['DELETE'])
        app.add_route(route_handler.delete_output, '/api/outputs/<id:int>', methods=['DELETE'])
        app.add_route(route_handler.delete_overlay, '/api/overlays/<id:int>', methods=['DELETE'])
        app.add_route(route_handler.delete_mixer, '/api/mixers/<id:int>', methods=['DELETE'])

        app.add_route(route_handler.cut_to_source, '/api/mixers/<id:int>/cut_to_source', methods=['POST'])
        app.add_route(route_handler.overlay_source, '/api/mixers/<id:int>/overlay_source', methods=['POST'])
        app.add_route(route_handler.remove_source, '/api/mixers/<id:int>/remove_source', methods=['POST'])

        app.add_route(route_handler.get_body, '/api/outputs/<id:int>/body')

        app.add_route(route_handler.restart, '/api/restart', methods=['POST'])
        app.add_route(route_handler.config_yaml, '/api/config/current.yaml', methods=['GET'])

        @app.websocket('/socket')
        async def feed(request, ws):
            await self.webockets_handler.feed(request, ws)

        def start_server():
            asyncio.set_event_loop(uvloop.new_event_loop())
            loop = asyncio.get_event_loop()
            server = app.create_server(host=config.api_host(), port=config.api_port(), access_log=False)
            asyncio.ensure_future(server)
            loop.create_task(self.webockets_handler.periodic_check())
            loop.run_forever()

        start_server()
