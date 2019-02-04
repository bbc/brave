//
// This web interface has been quickly thrown together. It's not production code.
//

preview = {
    outputId: null,
    source: null,
    type: null
}

preview.init = () => {
    $('#preview-bar-dropdown').click((change) => {
        preview._handlePreviewRequest($(change.target).data('type'), $(change.target).data('source'))
    })
    setInterval(preview._refreshImage, 500)
}

preview.handleOutputsUpdate = () => {
    preview._checkWeAreShowingTheRightOutput()
}

preview._checkWeAreShowingTheRightOutput = () => {
    outputId = preview._findRightOutputId()
    if (outputId !== preview.outputId) {
        preview._previewOutputId(preview.type, outputId)
    }
    preview._drawPreviewMenu()
}

preview._findRightOutputId = () => {
    if (preview.type === null || preview.source == null) return null
    const details = outputsHandler.findByDetails({type: preview.type, source: preview.source})
    return details ? details.id : null
}

preview._previewOutputId = (type, outputId) => {
    preview.outputId = outputId
    preview._delete()
    if (type === null || outputId === null) {
        // Do nothing
    }
    else if (type === 'webrtc') {
        webrtc.requestConnection(outputId)
    }
    else if (type === 'image') {
        preview._createImage()
    }
    else {
        console.error('Cannot preview type', type)
    }
}

preview._drawPreviewMenu = () => {
    let previewMsg = 'Off'
    const dropdownMenu = $('#preview-bar-dropdown')
    dropdownMenu.empty()
    const items = []
    const noPreviewOption = $('<a />').html('No preview')
    if (preview.source === null) {
        noPreviewOption.addClass('active')
    }
    items.push(noPreviewOption)

    const blockTypes = ['mixer', 'input']
    blockTypes.forEach(blockType => {
        const blockItems = blockType == 'input' ? inputsHandler.items : mixersHandler.items
        blockItems.forEach(item => {
            const webrtcPreview = $('<a />').data('source', item.uid).data('type', 'webrtc').html(prettyUid(item.uid) + ' (as a WebRTC stream)')
            const imagePreview = $('<a />').data('source', item.uid).data('type', 'image').html(prettyUid(item.uid) + ' (as an updating image)')
            if (preview.source === item.uid) {
                if (preview.type === 'webrtc') {
                    webrtcPreview.addClass('active')
                    previewMsg = webrtcPreview.html()
                }
                else if (preview.type === 'image') {
                    imagePreview.addClass('active')
                    previewMsg = imagePreview.html()
                }
            }
            items.push(webrtcPreview, imagePreview)
        })
    })

    items.forEach(i => {
        i.addClass('dropdown-item').attr('href', '#')
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

preview._handlePreviewRequest = (type, source) => {
    preview.source = source
    preview.type = type
    if (preview._findRightOutputId() === null && type !== null && source !== null) {
        outputsHandler.requestNewOutput({type, source})
    }
    preview._checkWeAreShowingTheRightOutput()
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
    var audioLevels = document.getElementById("audio_levels");
    if (audioLevels === null) return;
    var context = audioLevels.getContext("2d");
    var channels = websocket.volume.channels;
    var channel;
    var margin = 2;
    var width = 80;
    var height = audioLevels.clientHeight;
    var channelWidth = parseInt((width - (margin * (channels - 1))) / channels);
    var peak;

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
    audio_canvas.height = 270;

    $('#preview-bar').empty()
    $('#preview-bar').append(video)
    $('#preview-bar').append(audio_canvas)

    preview._showMuteButton()
    preview.updateAudioLevels();
}

preview._createImage = function() {
    const image = document.createElement('img')
    image.id = 'image-preview'
    $('#preview-bar').append(image)
}

preview.showErrorMessage = msg => {
    preview._delete()
    $('#preview-bar').append($('<p />').html('ERROR: ' + msg))
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
    $(image).attr('src', '/api/outputs/' + preview.outputId + '/body?' + Math.floor(Date.now()/100))
    const output = outputsHandler.findById(preview.outputId)
    if (output) {
        if (output.height && output.width) {
            let height = output.height
            let width = output.width
            const MAX_IMAGE_HEIGHT = 400
            if (output.height > MAX_IMAGE_HEIGHT) {
                const ratio = MAX_IMAGE_HEIGHT/height
                width *= ratio
                height = MAX_IMAGE_HEIGHT
            }
            $(image).attr('height', height)
            $(image).attr('width', width)
        }
    }
}

preview.init()
