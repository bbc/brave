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

preview._clamp = function(value, min = 0, max = 1) {
    return Math.min(Math.max(value, min), max);
}

preview._normaliseDb = function(db) {
    //  -60db -> 1.00 (very quiet)
    //  -30db -> 0.75
    //  -15db -> 0.50
    //  -5db -> 0.25
    //  -0db -> 0.00 (very loud)
    var logscale = 1 - Math.log10(-0.15 * db + 1);
    return preview._clamp(logscale);
}

preview._gradient = function(context, brightness, darkness, height) {
    var gradient = context.createLinearGradient(0, 0, 0, height);

    gradient.addColorStop(0.0, `rgb(${brightness}, ${darkness}, ${darkness})`);
    gradient.addColorStop(0.22, `rgb(${brightness}, ${brightness}, ${darkness})`);
    gradient.addColorStop(0.25, `rgb(${brightness}, ${brightness}, ${darkness})`);
    gradient.addColorStop(0.35, `rgb(${darkness}, ${brightness}, ${darkness})`);
    gradient.addColorStop(1.0, `rgb(${darkness}, ${brightness}, ${darkness})`);

    return gradient;
}

preview.updateAudioLevels = function() {
    var context = document.getElementById("audio_levels").getContext("2d");
    var channels = websocket.volume.channels;
    var channel;
    var margin = 2;
    var width = 80;
    var height = 360;
    var channelWidth = parseInt((width - (margin * (channels - 1))) / channels);
    var peak;

    //console.log(`width: ${width} filled with ${channels} channels of each ${channelWidth} and ${channels - 1} margin of ${margin}`);

    var bgFill = preview._gradient(context, 64, 0, height);
    var rmsFill =  preview._gradient(context, 255, 0, height);
    var peakFill = preview._gradient(context,  192, 0, height);
    var decayFill = preview._gradient(context,  255, 127, height);

    //Clear the canvas
    context.clearRect(0,0, width, height);

    for (channel = 0; channel < channels; channel++) {
        var audioData = JSON.parse(websocket.volume.data[channel]);

        var rms = preview._normaliseDb(audioData.rms) * height;
        peak = preview._normaliseDb(audioData.peak) * height;
        var decay = preview._normaliseDb(audioData.decay) * height;

        var x = (channel * channelWidth) + (channel * margin);

        //draw background
        context.fillStyle = bgFill;
        context.fillRect(x, 0, channelWidth, height - peak);

        // draw peak bar
        context.fillStyle = peakFill;
        context.fillRect(x, height - peak, channelWidth, peak);

        // draw rms bar below
        context.fillStyle = rmsFill;
        context.fillRect(x, height - rms, channelWidth, rms - peak);

        // draw decay bar
        context.fillStyle = decayFill;
        context.fillRect(x, height - decay, channelWidth, 2);

        // draw medium grey margin bar
        context.fillStyle = "gray";
        context.fillRect(x + channelWidth, 0, margin, height);
    }

    context.fillStyle= "white"
    context.font = "10px Arial";

    var dbMarkers = [-40, -20, -10, -5, -4, -3, -2, -1];
    dbMarkers.forEach(function(db) {
        var text = db.toString();
        var y = preview._normaliseDb(db) * height;
        var textwidth = context.measureText(text).width;
        var textheight = 10;

        if (y > peak) {
            context.fillStyle= "white";
        } else {
            context.fillStyle= "black";
        }
 
        context.fillText(text, (width - textwidth) - 2, height - y - textheight);
    });

    window.requestAnimationFrame( preview.updateAudioLevels );
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

    var audio_canvas = document.createElement('canvas')
    audio_canvas.id = 'audio_levels';
    audio_canvas.width  = 80;
    audio_canvas.height = 360;

    $('#preview-bar').empty()
    $('#preview-bar').append(video)
    $('#preview-bar').append(audio_canvas)

    preview._showMuteButton()
    preview.updateAudioLevels();
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
