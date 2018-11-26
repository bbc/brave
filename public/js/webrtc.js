//
// This web interface has been quickly thrown together. It's not production code.
//

webrtc = {}
const rtcConfig = {}
let sendChannel

webrtc.setIceServers = (s) => {
    console.log('New ice servers:', s)
    rtcConfig.iceServers = s
}

webrtc.requestConnection = (outputId) => {
    websocket.socket.send(JSON.stringify({msg_type:'webrtc-init', 'output_id': outputId}))
}

webrtc.close = () => {
    if (webrtc.peerConnection) {
        console.log('Closing webrtc connection')
        webrtc.peerConnection.close();
        webrtc.peerConnection = null;

        // webrtcbin does not catch a close connection, so we tell Brave directly:
        websocket.socket.send(JSON.stringify({msg_type:'webrtc-close'}))
    }
}

webrtc.createCall = function() {
    console.log('Creating RTCPeerConnection');

    webrtc.peerConnection = new RTCPeerConnection(rtcConfig);
    sendChannel = webrtc.peerConnection.createDataChannel('label', null);
    sendChannel.onopen = handleDataChannelOpen;
    sendChannel.onmessage = handleDataChannelMessageReceived;
    sendChannel.onerror = handleDataChannelError;
    sendChannel.onclose = handleDataChannelClose;
    webrtc.peerConnection.ondatachannel = onDataChannel;
    webrtc.peerConnection.onaddstream = onRemoteStreamAdded;

    webrtc.peerConnection.oniceconnectionstatechange = () => {
        if (webrtc.peerConnection) {
            console.log('New ICE connection state:', webrtc.peerConnection.iceConnectionState)
        }
    }

    webrtc.peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
            console.debug('ICE candidate:', event.candidate)
            websocket.socket.send(JSON.stringify({'ice': event.candidate}))
	    }
        else {
            console.log('ICE gathering finished')
        }
    }

    console.log('Created peer connection for call, awaiting SDP');
}


// SDP offer received from peer, set remote description and create an answer
webrtc.onIncomingSDP = function(sdp) {
    console.log('Got sdp:', sdp)

    if (!webrtc.peerConnection)
        webrtc.createCall();

    webrtc.peerConnection.setRemoteDescription(sdp).then(() => {
        if (sdp.type != "offer")
            return;
        webrtc.peerConnection.createAnswer()
        .then(webrtc.onLocalDescription).catch(showMessage);
    }).catch(showMessage);
}

// Local description was set, send it to peer
webrtc.onLocalDescription = function(desc) {
    console.log("Got local description: " + JSON.stringify(desc));
    webrtc.peerConnection.setLocalDescription(desc).then(function() {
        console.log("Sending SDP answer");
        sdp = {'sdp': webrtc.peerConnection.localDescription}
        websocket.socket.send(JSON.stringify(sdp));
    });
}

// ICE candidate received from peer, add it to the peer connection
webrtc.onIncomingICE = function(ice) {
    var candidate = new RTCIceCandidate(ice);
    webrtc.peerConnection.addIceCandidate(candidate).catch(showMessage);
}

const handleDataChannelOpen = (event) =>{
    console.log("dataChannel.OnOpen", event);
};

const handleDataChannelMessageReceived = (event) =>{
    console.log("dataChannel.OnMessage:", event, event.data.type);

    console.log("Received data channel message");
    if (typeof event.data === 'string' || event.data instanceof String) {
        console.log('Incoming string message: ' + event.data);
        textarea = document.getElementById("text")
        textarea.value = textarea.value + '\n' + event.data
    } else {
        console.log('Incoming data message');
    }
    sendChannel.send('Hi from client');
};

const handleDataChannelError = (error) =>{
    console.error('dataChannel.OnError:', error);
};

const handleDataChannelClose = (event) =>{
    console.error('dataChannel.OnClose', event);
};

function errorUserMediaHandler() {
    showMessage('WebRTC not suppoeted by this browser', 'warning');
}

function onDataChannel(event) {
    console.log("Data channel created");
    let receiveChannel = event.channel;
    receiveChannel.onopen = handleDataChannelOpen;
    receiveChannel.onmessage = handleDataChannelMessageReceived;
    receiveChannel.onerror = handleDataChannelError;
    receiveChannel.onclose = handleDataChannelClose;
}

function onRemoteStreamAdded(event) {
    videoTracks = event.stream.getVideoTracks();
    audioTracks = event.stream.getAudioTracks();

    if (videoTracks.length > 0) {
        console.log('Incoming stream: ' + videoTracks.length + ' video tracks and ' + audioTracks.length + ' audio tracks');
        preview.setVideoSrc(event.stream)
    } else {
        console.error('Stream with unknown tracks added');
    }
}

function getLocalStream() {
    if (navigator.mediaDevices.getUserMedia) {
        return navigator.mediaDevices.getUserMedia({video: true, audio: true});
    } else {
        errorUserMediaHandler();
    }
}
