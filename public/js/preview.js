//
// This web interface has been quickly thrown together. It's not production code.
//

preview = {}

preview.init = () => {
    $('#preview-bar-dropdown').click((change) => {
        preview._handlePreviewRequest($(change.target).data('val'))
    })
    setInterval(preview._refreshImage, 1000)
}

preview.previewOutput = (type, outputId) => {
    if (preview.currentlyPreviewingOutputId === outputId) return
    preview.currentlyPreviewingOutputId = outputId
    preview.drawPreviewMenu()
    preview._delete()
    if (type === null) {
        // Do nothing
    }
    if (type === 'webrtc') {
        webrtc.requestConnection(outputId)
    }
    else if (type === 'image') {
        preview._createImage()
    }
    else {
        console.error('Cannot preview type', type)
    }
}

preview.drawPreviewMenu = function() {
    let previewMsg = 'Off'
    const dropdownMenu = $('#preview-bar-dropdown')
    dropdownMenu.empty()
    const items = []
    items.push($('<a />').html('No preview'))

    var webrtcOutputs = outputsHandler.items.filter(o => o.type === 'webrtc')
    if (!webrtcOutputs.length) {
        items.push($('<a />').data('val', 'webrtc').html('WebRTC'))
    }
    else {
        webrtcOutputs.forEach(o => {
            items.push($('<a />').data('val', o.id).html('Output ' + o.id + ' (WebRTC stream)'))
        })
    }

    var imageOutputs = outputsHandler.items.filter(o => o.type === 'image')
    if (!imageOutputs.length) {
        items.push($('<a />').data('val', 'image').html('Updating image'))
    }
    else {
        imageOutputs.forEach(o => {
            items.push($('<a />').data('val', o.id).html('Output ' + o.id + ' (updating image)'))
        })
    }

    items.forEach(i => {
        i.addClass('dropdown-item').attr('href', '#')
        if (preview.currentlyPreviewingOutputId === i.data('val')) {
            i.addClass('active')
            previewMsg = i.html()
        }
    })

    dropdownMenu.append(items)
    $('#preview-button-msg').html('Preview: ' + previewMsg)
}

preview._showMuteButton = () => {
    const player = $(preview._getVideoPlayer())
    const muted = player.prop('muted')
    preview._removeMuteButton()
    const muteButton = muted ? components.mutedButton() : components.unmutedButton()
    muteButton.attr('id', 'mute-button')
    muteButton.click(() => {
        player.prop('muted', !player.prop('muted'));
        preview._showMuteButton();
        return false
    })
    $('#mute-span').empty().append(muteButton)
}

preview._removeMuteButton = () => {
    const currentButton = $('#mute-button')
    if (currentButton && currentButton.length) currentButton.remove()
}

preview._handlePreviewRequest = function(request) {
    if (request === 'webrtc') {
        outputsHandler._requestNewWebRtcOutput()
    }
    else if (request === 'image') {
        outputsHandler._requestNewImageOutput()
    }
    else if (!isNaN(parseInt(request))) {
        const outputId = parseInt(request)
        const output = outputsHandler.findById(outputId)
        if (!output) {
            console.error('Cannot find output ID', outputId, 'in output list:', outputsHandler.items)
            return
        }
        const type = output.type
        preview.previewOutput(type, outputId)
    }
    else {
        preview.previewOutput(null, null)
    }
}

preview.setVideoSrc = function(src) {
    preview._createVideoPlayer()
    getVideoElement().srcObject = src;
}

preview._getImage = () => {
    return $('#image-preview');
}

preview._getVideoPlayer = function() {
    return document.getElementById('stream');
}

preview._createVideoPlayer = function() {
    var video = document.createElement('video')
    video.id = 'stream'
    video.autoplay = true
    $('#preview-bar').empty()
    $('#preview-bar').append(video)
    preview._showMuteButton()
}

preview._createImage = function() {
    const image = document.createElement('img')
    image.id = 'image-preview'
    $(image).attr('src', 'output_images/img.jpg?' + Math.floor(Date.now()/1000) )
    $('#preview-bar').append(image)
}

preview._delete = () => {
    preview._deleteVideoPlayer()
    $('#preview-bar').empty()
}

preview._deleteVideoPlayer = () => {
    const currentElement = $(preview._getVideoPlayer())
    if (!currentElement || !currentElement.length) return
    webrtc.close()
    var videoElement = preview._getVideoPlayer();
    if (videoElement) {
        videoElement.pause();
        videoElement.src = "";
        videoElement.load();
    }
    $('#preview-bar').empty()
    preview._removeMuteButton()
}

preview._refreshImage = () => {
    const image = preview._getImage()
    if (!image || !image.length) return
    $(image).attr('src', 'output_images/img.jpg?' + Math.floor(Date.now()/1000) )
}

preview.init()
