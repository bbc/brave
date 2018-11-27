from brave.outputs.output import Output
from gi.repository import Gst
import brave.config as config
import json
import asyncio
import gi
import websockets
gi.require_version('GstWebRTC', '1.0')
from gi.repository import GstWebRTC
gi.require_version('GstSdp', '1.0')
from gi.repository import GstSdp


class WebRTCOutput(Output):
    '''
    For sending to a client (peer) audio/video as WebRTC.
    '''

    def __init__(self, **args):
        super().__init__(**args)
        self.overall_peer_count = 0
        self.peers = {}

    def permitted_props(self):
        return {
            **super().permitted_props(),
            'width': {
                'type': 'int',
                'default': 480
            },
            'height': {
                'type': 'int',
                'default': 270
            }
        }

    def create_elements(self):
        self._create_initial_multiqueue()

        if not self._create_pipeline():
            return False

        if config.enable_video():
            self.intervideosrc = self.pipeline.get_by_name('intervideosrc')
            self.intervideosrc_src_pad = self.intervideosrc.get_static_pad('src')
            self.create_intervideosink_and_connections()

        if config.enable_audio():
            self.interaudiosrc = self.pipeline.get_by_name('interaudiosrc')
            self.interaudiosrc_src_pad = self.interaudiosrc.get_static_pad('src')
            self.create_interaudiosink_and_connections()

        self.webrtc_video_tee = self.pipeline.get_by_name('webrtc_video_tee')
        self.webrtc_audio_tee = self.pipeline.get_by_name('webrtc_audio_tee')

        return True

    def _create_pipeline(self):
        '''
        Create the pipeline. This will not have the webrtcbin element in it.
        That is added when a user tries to connect, via new_peer_request().
        Instead, a 'fakesink' destination allows the pipeline to work even with 0 clients.
        '''
        pipeline_string = ''
        if config.enable_video():
            # format=RGB is required to remove alpha channels which can upset the encoder
            video_caps = 'application/x-rtp,format=RGB,media=video,encoding-name=VP8,payload=97,width=%d,height=%d' % \
                (self.props['width'], self.props['height'])

            # vp8enc has 'target-bitrate' which can be reduced from its default (256000)
            # Setting keyframe-max-dist lower reduces impact of packet loss on dodgy networks
            pipeline_string += ('intervideosrc name=intervideosrc ! queue ! videoconvert ! videoscale ! '
                                'vp8enc deadline=1 keyframe-max-dist=30 ! rtpvp8pay ! ' + video_caps +
                                ' ! tee name=webrtc_video_tee webrtc_video_tee. ! fakesink')
        if config.enable_audio():
            # bandwidth=superwideband allows the encoder to focus a little more on the important audio
            # (Basic testing showed 'wideband' to be quite poor poor)
            pipeline_string += (' interaudiosrc name=interaudiosrc ! audioconvert ! level message=true ! '
                                'audioresample name=webrtc-audioresample ! opusenc bandwidth=superwideband  ! '
                                'rtpopuspay ! application/x-rtp,media=audio,encoding-name=OPUS,payload=96 ! '
                                'tee name=webrtc_audio_tee webrtc_audio_tee. ! fakesink')

        if not self.create_pipeline_from_string(pipeline_string):
            return False

        self.pipeline.get_bus().add_signal_watch()
        self.pipeline.get_bus().connect('message::element', self._on_element_message)
        self.event_loop = asyncio.get_event_loop()
        return True

    def _update_current_num_peers(self):
        self.current_num_peers = len(self.peers)
        self.logger.info('I now have %d peers', self.current_num_peers)

    async def new_peer_request(self, ws):
        '''
        Called when a peer (client) would like to connect via webrtc
        '''
        if ws in self.peers:
            self.logger.debug('Existing user requesting webrtc again, so removing old one')
            await self.remove_peer_request(ws)

        self.peers[ws] = {}
        self._update_current_num_peers()
        await ws.send(json.dumps({'msg_type': 'webrtc-initialising', 'ice_servers': config.ice_servers()}))

        self._create_webrtc_element_for_new_connection(ws)

        self.peers[ws]['webrtcbin'].connect('on-negotiation-needed', self._on_negotiation_needed, ws)
        self.peers[ws]['webrtcbin'].connect('on-ice-candidate', self._send_ice_candidate_message, ws)
        # In the future, use connect('pad-added' here if the client's return video is wanted

        if not self.pipeline.set_state(Gst.State.PLAYING):
            self.logger.warn('Unable to enter PLAYING state now that we have a peer')
        else:
            self.logger.debug('Successfully added a new peer request')

    def _on_element_message(self, bus, message):
        if len(self.peers) == 0:
            return
        t = message.type
        if t == Gst.MessageType.ELEMENT:
            if message.get_structure().get_name() == 'level':
                channels = len(message.get_structure().get_value('peak'))
                data = []

                for i in range(0, channels):
                    data.append(json.dumps({
                        'peak': message.get_structure().get_value('peak')[i],
                        'rms': message.get_structure().get_value('rms')[i],
                        'decay': message.get_structure().get_value('decay')[i]
                    }))

                jsonData = json.dumps({'msg_type': 'volume', 'channels': channels, 'data': data})
                self.event_loop.create_task(self._send_data_to_all_peers(jsonData))

    async def _send_data_to_all_peers(self, jsonData):
        for ws in self.peers:
            try:
                await ws.send(jsonData)
            except websockets.ConnectionClosed:
                pass

    async def remove_peer_request(self, ws):
        '''
        Called when a peer (client) disconnects.
        '''
        if ws not in self.peers:
            self.logger.warn('remove_peer_request called but this is not a peer')
            return

        self._remove_no_longer_needed_tee_pads(ws)
        self._remove_webrtc_element(ws)
        del self.peers[ws]
        self._update_current_num_peers()

    def _create_webrtc_element_for_new_connection(self, ws):
        '''
        We make a new webrtc element, and queue to feed into it, for every new peer (client).
        That way, multiple clients can connect at once.
        '''

        self.peers[ws]['webrtcbin'] = Gst.ElementFactory.make('webrtcbin')
        self.pipeline.add(self.peers[ws]['webrtcbin'])
        self.peers[ws]['webrtcbin'].add_property_notify_watch(None, True)
        if len(config.ice_servers()) > 0:
            ice_server_url = config.ice_servers()[0]['urls']
            self.peers[ws]['webrtcbin'].set_property('stun-server', ice_server_url)

        if config.enable_video():
            self.peers[ws]['video_queue'] = Gst.ElementFactory.make('queue')
            self.pipeline.add(self.peers[ws]['video_queue'])
            self.webrtc_video_tee.link(self.peers[ws]['video_queue'])
            self.peers[ws]['video_queue'].link(self.peers[ws]['webrtcbin'])

        if config.enable_audio():
            self.peers[ws]['audio_queue'] = Gst.ElementFactory.make('queue')
            self.pipeline.add(self.peers[ws]['audio_queue'])
            self.webrtc_audio_tee.link(self.peers[ws]['audio_queue'])
            self.peers[ws]['audio_queue'].link(self.peers[ws]['webrtcbin'])

    def _remove_webrtc_element(self, ws):
        '''
        When deleting a connection, delete the webrtc element and the queue before it.
        (If the user reconnects, we'll create a new one.)
        '''
        for element_name in ['webrtcbin', 'video_queue', 'audio_queue']:
            if element_name in self.peers[ws]:
                element = self.peers[ws][element_name]
                if not element.set_state(Gst.State.NULL) or not hasattr(self, 'pipeline') \
                   or not self.pipeline.remove(element):
                    self.logger.warn('Cannot remove ' + element_name)

    def _remove_no_longer_needed_tee_pads(self, ws):
        '''
        When deleting a connection, the audio and tees will have src (output) pads
        that are no longer required. This deletes them.
        '''
        for av in ['video', 'audio']:
            element_name = av + '_queue'
            if element_name in self.peers[ws]:
                element = self.peers[ws][element_name]
                sink_pad = element.get_static_pad('sink')
                tee_pad_to_remove = sink_pad.get_peer()
                if tee_pad_to_remove:
                    tee = getattr(self, 'webrtc_%s_tee' % av)
                    if not tee.remove_pad(tee_pad_to_remove):
                        self.logger.warn('Unable to remove pad from %s tee' % av)

    async def sdp_message_from_peer(self, ws, sdp):
        '''
        Called when the peer (client) has sent (via websocket) an SDP message
        '''
        assert(sdp['type'] == 'answer')
        sdp = sdp['sdp']
        res, sdpmsg = GstSdp.SDPMessage.new()
        GstSdp.sdp_message_parse_buffer(bytes(sdp.encode()), sdpmsg)
        answer = GstWebRTC.WebRTCSessionDescription.new(GstWebRTC.WebRTCSDPType.ANSWER, sdpmsg)
        promise = Gst.Promise.new()
        self.peers[ws]['webrtcbin'].emit('set-remote-description', answer, promise)
        promise.interrupt()

    async def ice_message_from_peer(self, ws, ice):
        '''
        Called when the peer (client) has sent (via websocket) an ICE message
        '''
        self.peers[ws]['webrtcbin'].emit('add-ice-candidate', ice['sdpMLineIndex'], ice['candidate'])

    def _send_sdp_offer(self, offer, ws):
        text = offer.sdp.as_text()
        self.logger.debug('Sending SDP offer to client (%d chars in length)' % len(text))
        msg = json.dumps({'sdp': {'type': 'offer', 'sdp': text}})
        loop = asyncio.new_event_loop()
        loop.run_until_complete(ws.send(msg))

    def _on_offer_created(self, promise, webrtcbin, ws):
        promise.wait()
        reply = promise.get_reply()
        offer = reply.get_value('offer')
        promise = Gst.Promise.new()
        webrtcbin.emit('set-local-description', offer, promise)
        promise.interrupt()
        self._send_sdp_offer(offer, ws)

    def _on_negotiation_needed(self, element, ws):
        promise = Gst.Promise.new_with_change_func(self._on_offer_created, element, ws)
        element.emit('create-offer', None, promise)

    def _send_ice_candidate_message(self, _, mlineindex, candidate, ws):
        '''
        Called when this server wishes to propose an ICE candidate to the client.
        '''
        icemsg = json.dumps({'ice': {'candidate': candidate, 'sdpMLineIndex': mlineindex}})
        loop = asyncio.new_event_loop()
        loop.run_until_complete(ws.send(icemsg))
