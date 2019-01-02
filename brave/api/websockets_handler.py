import websockets
import asyncio
import json
import brave.helpers
import psutil
from brave.outputs.webrtc import WebRTCOutput
logger = brave.helpers.get_logger('websockets')


class WebsocketsHandler():
    '''
    Class to handle websockets to clients
    '''

    def __init__(self, session):
        self.session = session
        self._websocket_clients = []

    async def send_message_to_first_client(self, m):
        ws = self._websocket_clients[0]
        await ws.send(json.dumps({'msg': m}))

    async def feed(self, request, ws):
        self._websocket_clients.append(ws)

        logger.debug('New websocket client... I now have %d websocket clients' % len(self._websocket_clients))

        async def heartbeat():
            try:
                HEARTBEAT_PERIOD = 5
                while True:
                    await ws.send(json.dumps({'msg_type': 'ping', 'cpu_percent': psutil.cpu_percent(interval=0)}))
                    await asyncio.sleep(HEARTBEAT_PERIOD)
            except websockets.ConnectionClosed:
                if ws in self._websocket_clients:
                    self._websocket_clients.remove(ws)
                if hasattr(ws, 'webrtc_output'):
                    await ws.webrtc_output.remove_peer_request(ws)
                    delattr(ws, 'webrtc_output')
                # await output.remove_peer_request()

        asyncio.ensure_future(heartbeat())
        while True:
            data_json = await ws.recv()
            data = json.loads(data_json)
            if ('msg_type' in data and data['msg_type'] == 'pong'):
                pass
            elif ('msg_type' in data and data['msg_type'] == 'webrtc-init'):
                if 'output_id' not in data or data['output_id'] is None:
                    await ws.send(json.dumps({'error': 'no output_id'}))
                    return

                try:
                    output_id = int(data['output_id'])
                except ValueError:
                    await ws.send(json.dumps({'error': 'output_id not an integer'}))
                    return

                if type(self.session.outputs[output_id]) != WebRTCOutput:
                    await ws.send(json.dumps({'error': 'webrtc-init called on output that is not WebRTC'}))
                    return

                try:
                    ws.webrtc_output = self.session.outputs[output_id]
                except KeyError:
                    await ws.send(json.dumps({'error': 'no such id'}))
                    return
                await ws.webrtc_output.new_peer_request(ws)

            # Allow the client to report when it does not want webrtc anymore:
            elif ('msg_type' in data and data['msg_type'] == 'webrtc-close'):
                if hasattr(ws, 'webrtc_output'):
                    await ws.webrtc_output.remove_peer_request(ws)
                    delattr(ws, 'webrtc_output')

            elif 'sdp' in data:
                await ws.webrtc_output.sdp_message_from_peer(ws, data['sdp'])
            elif 'ice' in data:
                await ws.webrtc_output.ice_message_from_peer(ws, data['ice'])
            else:
                logger.warning('Unknown websocket message from client:' + data_json)

    async def periodic_check(self):
        while True:
            UPDATE_PERIOD = 0.1
            try:
                messages_to_send = await self.check_for_items_recently_updated()
                messages_to_send.extend(await self.check_for_items_recently_deleted())
                await self.send_to_all_clients(messages_to_send)
            except Exception as e:
                logger.warning('Error on periodic websocket check:' + str(e))
            await asyncio.sleep(UPDATE_PERIOD)

    async def check_for_items_recently_updated(self):
        items_recently_updated = set(self.session.items_recently_updated)
        self.session.items_recently_updated = []
        messages_to_send = []
        for o in items_recently_updated:
            messages_to_send.append({
                'msg_type': 'update',
                'block_type': o.input_output_overlay_or_mixer(),
                'data': o.summarise()
            })
        return messages_to_send

    async def check_for_items_recently_deleted(self):
        messages_to_send = []
        for item in self.session.items_recently_deleted:
            messages_to_send.append({
                'msg_type': 'delete',
                'block_type': item['block_type'],
                'id': item['id']
            })
        self.session.items_recently_deleted = []
        return messages_to_send

    async def send_to_all_clients(self, messages_to_send):
        for msg in messages_to_send:
            for ws in self._websocket_clients:
                try:
                    await ws.send(json.dumps(msg))
                except websockets.ConnectionClosed:
                    self._websocket_clients.remove(ws)
