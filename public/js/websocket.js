//
// This web interface has been quickly thrown together. It's not production code.
//

websocket = {
    setupErrorCount: 0,
    volume: {channels: 0, data: [] },
}

websocket.setup = function() {
    var hostAndPort = window.location.host
    var protocol = window.location.protocol == 'http:' ? 'ws:' : 'wss:'
    var websocketUrl = protocol + '//' + hostAndPort + '/socket'
    websocket.socket = new WebSocket(websocketUrl)
    websocket.socket.addEventListener('open', websocket._onSocketOpen)
    websocket.socket.addEventListener('error', websocket._onSocketError);
    websocket.socket.addEventListener('message', websocket._onMessageReceived);
    websocket.socket.addEventListener('close', websocket._onSocketClose);
}

websocket._onSocketOpen = event => {
    websocket.setupErrorCount = 0
}

websocket._onSocketError = event => {
    websocket.setupErrorCount++
}

websocket._onSocketClose = event => {
    console.log('Websocket closed, reconnecting...')
    var NUM_RETRY_ATTEMPTS = 10
    if (websocket.setupErrorCount < NUM_RETRY_ATTEMPTS) {
        console.error("Websocket error, now happened " + websocket.setupErrorCount + ' times')
        showMessage('Server connection lost, retrying...')
        window.setTimeout(websocket.setup, 1000 + (1000 * websocket.setupErrorCount));
    }
    else {
        console.error("Websocket error, now happened " + websocket.setupErrorCount + ' times, not attempting again.')
        showMessage('Unable to connect to server, please refresh the page')
    }
}

websocket._onMessageReceived = event => {
    dataParsed = JSON.parse(event.data)
    if (dataParsed.msg_type === 'ping') {
        if (dataParsed.cpu_percent) {
            websocket._setCpuPercent(dataParsed.cpu_percent)
        }
        return
    }
    else if (dataParsed.msg_type === 'update') {
        websocket._handleUpdate(dataParsed)
    }
    else if (dataParsed.msg_type === 'delete') {
        websocket._handleDelete(dataParsed)
    }
    else if (dataParsed.msg_type === 'webrtc-initialising') {
        if (dataParsed.ice_servers) webrtc.setIceServers(dataParsed.ice_servers)
    }
    else if (dataParsed.msg_type === 'volume') {
        websocket.volume.channels = dataParsed.channels;
        websocket.volume.data = dataParsed.data;
    }
    else if (dataParsed.sdp != null) {
        webrtc.onIncomingSDP(dataParsed.sdp);
    } else if (dataParsed.ice != null) {
        webrtc.onIncomingICE(dataParsed.ice);
    } else {
        console.warning("Unexpected websocket message:", dataParsed);
    }
}

websocket._getHandlerForBlockType = function(t) {
    switch(t) {
        case 'input':
            return inputsHandler
        case 'output':
            return outputsHandler
        case 'mixer':
            return mixersHandler
        case 'overlay':
            return overlaysHandler
    }

    console.error('Unknown block type', t)
}

websocket._handleUpdate = function(item) {
    var handler = websocket._getHandlerForBlockType(item.block_type)
    if (handler) {
        handler.items = handler.items.filter(x => x.id != item.data.id)
        handler.items.push(item.data)
        handler.items.sort((a,b) => a.id - b.id)
        drawAllItems()
    }
}

websocket._handleDelete = function(item) {
    var handler = websocket._getHandlerForBlockType(item.block_type)
    if (handler) {
        handler.items = handler.items.filter(x => x.id != item.id)
        drawAllItems()
    }
}

websocket._setCpuPercent = (num) => {
    $('#cpu-stats').empty().html('CPU usage: ' + num + '%')
}
