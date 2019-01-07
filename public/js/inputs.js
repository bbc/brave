//
// This web interface has been quickly thrown together. It's not production code.
//
inputsHandler = {}
inputsHandler.items = []

inputsHandler.draw = function() {
    inputsHandler._drawCards()
}

inputsHandler.findById = function(id) {
    return inputsHandler.items.find(function(x) { return x.id == id })
}

inputsHandler.showFormToAdd = function() {
    inputsHandler._showForm({})
}

inputsHandler.showFormToEdit = function(input) {
    inputsHandler._showForm(input)
}

inputsHandler.seek = function(input) {
    var end = input.duration/1000000000
    secondsSeek = prompt("What should input " + input.id + "seek to, in seconds. (0=start, " + end + "=end)");
    inputsHandler._submitCreateOrEdit(input.id, {position:secondsSeek*1000000000})
}

inputsHandler._drawCards = () => {
    $('#cards').append(inputsHandler.items.map(inputsHandler._asCard))
}

inputsHandler._asCard = (input) => {
    return components.card({
        title: prettyUid(input.uid) + ' (' + prettyType(input.type) + ')',
        options: inputsHandler._optionButtonsForInput(input),
        body: inputsHandler._inputCardBody(input),
        state: components.stateBox(input, inputsHandler.setState),
        mixOptions: components.getMixOptions(input)
    })
}

inputsHandler._optionButtonsForInput = (input) => {
    var editButton   = components.editButton().click(() => { inputsHandler.showFormToEdit(input); return false })
    var deleteButton = components.deleteButton().click(() => { inputsHandler.delete(input); return false })
    var seekButton   = components.seekButton().click(() => { inputsHandler.seek(input); return false })
    return [editButton, deleteButton, seekButton]
}

inputsHandler._inputCardBody = (input) => {
    var details = []
    if (input.props.uri) details.push('<div><code>' + input.props.uri + '</code></div>')
    if (input.hasOwnProperty('width') &&
        input.hasOwnProperty('height')) details.push('<strong>Input size:</strong> ' + prettyDimensions(input))
    if (input.props.hasOwnProperty('width') &&
        input.props.hasOwnProperty('height')) details.push('<div><strong>Resized to:</strong> ' + prettyDimensions(input.props) + '</div>')
    if (input.hasOwnProperty('framerate')) details.push('<div><strong>Framerate:</strong> ' + Math.round(input.framerate) + '</div>')
    if (input.props.hasOwnProperty('xpos') && input.props.hasOwnProperty('ypos')) details.push('<div><strong>Position on screen:</strong> ' + input.props.xpos + 'x' + input.props.ypos + '</div>')
    if (input.props.hasOwnProperty('zorder')) details.push('<strong>Z-order:</strong> ' + input.props.zorder)
    if (input.hasOwnProperty('audio_channels')) details.push('<div><strong>Audio channels:</strong> ' + input.audio_channels + '</div>')
    if (input.hasOwnProperty('audio_rate')) details.push('<div><strong>Audio rate:</strong> ' + input.audio_rate + '</div>')
    if (input.props.hasOwnProperty('volume')) details.push('<div><strong>Volume:</strong> ' + (100 * input.props.volume) + '&#37;</div>')
    if (input.props.hasOwnProperty('input_volume')) details.push('<div><strong>Input volume:</strong> ' + input.props.input_volume + '</div>')
    if (input.props.hasOwnProperty('freq')) details.push('<div><strong>Frequency:</strong> ' + input.props.freq + 'Hz</div>')
    if (input.props.hasOwnProperty('pattern')) details.push('<div><strong>Pattern:</strong> ' + inputsHandler.patternTypes[input.props.pattern] + '</div>')
    if (input.props.hasOwnProperty('wave')) details.push('<div><strong>Wave:</strong> ' + inputsHandler.waveTypes[input.props.wave] + '</div>')
    if (input.props.hasOwnProperty('device')) details.push('<div><strong>Device Num:</strong> ' + input.props.device + '</div>')
    if (input.props.hasOwnProperty('connection')) details.push('<div><strong>Connection Type:</strong> ' + inputsHandler.decklinkConnection[input.props.connection] + '</div>')
    if (input.props.hasOwnProperty('mode')) details.push('<div><strong>Input Mode:</strong> ' + inputsHandler.decklinkModes[input.props.mode] + '</div>')

    if (input.hasOwnProperty('duration')) {
        var duration = prettyDuration(input.duration)
        if (duration !== null) details.push('<strong>duration:</strong> ' + duration)
    }

    if (input.hasOwnProperty('error_message')) details.push('<strong>ERROR:</strong> <span style="color:red">' + input.error_message + '</span>')
    return details.map(d => $('<div></div>').append(d))
}

inputsHandler._handleNewFormType = function(event) {
    inputsHandler._populateForm({type: event.target.value})
}

inputsHandler._showForm = function(input) {
    inputsHandler.currentForm = $('<form></form>')
    var label = input && input.hasOwnProperty('id') ? 'Edit input ' + input.id : 'Add input'
    showModal(label, inputsHandler.currentForm, inputsHandler._handleFormSubmit)
    inputsHandler._populateForm(input)
}

inputsHandler._populateForm = function(input) {
    var form = inputsHandler.currentForm
    form.empty()
    if (!input.props) input.props = {}

    var uriExamples = ''
    if (input.type && input.type === 'uri') {
        uriExamples = 'RTMP example: <code>rtmp://184.72.239.149/vod/BigBuckBunny_115k.mov</code></div>' +
        '<div>RTSP example: <code>rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov</code></div>' +
        '<div>Example: <code>file:///tmp/my_movie.mp4</code>'
    }
    else if (input.type && input.type === 'image') {
        uriExamples = 'Enter a local or URL location of a JPG, PNG, or SVG file.'
    }

    var positionBox = formGroup({
        id: 'input-position',
        label: 'Position (&lt;width&gt;x&lt;height&gt;)',
        name: 'position',
        type: 'text',
        value: (input.props.xpos || 0) + 'x' + (input.props.ypos || 0),
        help: 'In the format <samp>&lt;width&gt;x&lt;height&gt;</samp>. The default, <samp>0x0</samp>, puts it in the top-left corner.'
    })

    var zOrderBox = formGroup({
        id: 'input-zorder',
        label: 'Z-order',
        name: 'zorder',
        type: 'number',
        value: input.props.zorder || inputsHandler.getNextZorder()
    })

    var uriRow = formGroup({
        id: 'input-uri',
        label: 'Location (URI)',
        name: 'uri',
        type: 'text',
        value: input.props.uri || '',
        help: uriExamples,
    })

    var sizeBox = getDimensionsSelect('dimensions', input.props.width, input.props.height)

    var patternBox = formGroup({
        id: 'input-pattern',
        label: 'Pattern',
        name: 'pattern',
        options: inputsHandler.patternTypes,
        initialOption: 'Select a pattern...',
        value: input.props.pattern || inputsHandler.patternTypes[0]
    })

    var waveBox = formGroup({
        id: 'input-wave',
        label: 'Waveform',
        name: 'wave',
        options: inputsHandler.waveTypes,
        initialOption: 'Select a wave...',
        value: input.props.wave || inputsHandler.waveTypes[0]
    })

    var freqBox = formGroup({
        id: 'input-freq',
        label: 'Frequency (Hz)',
        name: 'freq',
        type: 'number',
        value: input.props.freq || 440,
        min: 20,
        step: 100,
        max: 20000
    })

    var device = formGroup({
        id: 'input-device',
        label: 'Device Num',
        name: 'device',
        type: 'number',
        value: input.props.device || 0
    })

    var connection = formGroup({
        id: 'connection-device',
        label: 'Connection Type',
        name: 'connection',
        type: 'number',
        options: inputsHandler.decklinkConnection,
        initialOption: 'Select connection type',
        value: input.props.connection || inputsHandler.decklinkConnection[1]
    })

    var mode = formGroup({
        id: 'mode-device',
        label: 'Input Mode',
        name: 'mode',
        type: 'number',
        options: inputsHandler.decklinkModes,
        initialOption: 'Select input mode',
        value: input.props.mode || inputsHandler.decklinkModes[17]
    })

    var isNew = !input.hasOwnProperty('id')
    if (isNew) {
        var options = {
            'uri': 'URI (for files, RTMP, RTSP and HLS)',
            'image': 'Image',
            'html': 'HTML (for showing a web page)',
            'decklink': 'Decklink Device',
            'test_video': 'Test video stream',
            'test_audio': 'Test audio stream',
        }
        form.append(formGroup({
            id: 'input-type',
            label: 'Type',
            name: 'type',
            initialOption: 'Select a type...',
            options,
            value: input.type
        }))
    }
    else {
        form.append('<input type="hidden" name="id" value="' + input.id + '">')
    }

    if (!input.type) {
    }
    else if (input.type === 'test_audio') {
        form.append();
        form.append(components.volumeInput(input.props.volume));
        form.append(waveBox);
        form.append(freqBox);
    }
    else if (input.type === 'test_video') {
        form.append(patternBox);
        form.append(positionBox);
        form.append(sizeBox);
        form.append(zOrderBox);
    }
    else if (input.type === 'image') {
        if (isNew) form.append(uriRow);
        form.append(positionBox);
        form.append(sizeBox);
        form.append(zOrderBox);
    }
    else if (input.type === 'uri') {
        if (isNew) form.append(uriRow);
        form.append(positionBox);
        form.append(sizeBox);
        form.append(zOrderBox);
        form.append(components.volumeInput(input.props.volume));
    }
    else if (input.type === 'html') {
        if (isNew) form.append(uriRow);
        form.append(positionBox);
        form.append(sizeBox);
        form.append(zOrderBox);
    }
    else if (input.type === 'decklink') {
        if (isNew) form.append(device);
        if (isNew) form.append(mode);
        if (isNew) form.append(connection);
        form.append(positionBox);
        form.append(sizeBox);
        form.append(zOrderBox);
    }
    form.find('select[name="type"]').change(inputsHandler._handleNewFormType);
}

inputsHandler._handleFormSubmit = function() {
    var form = inputsHandler.currentForm
    var idField = form.find('input[name="id"]')
    var id = idField.length ? idField.val() : null
    var input = (id != null) ? inputsHandler.findById(id) : {}
    var newProps = {}

    fields = ['type', 'uri', 'position', 'zorder', 'dimensions', 'freq', 'volume', 'input_volume', 'pattern', 'wave']
    fields.forEach(function(f) {
        var input = form.find('[name="' + f + '"]')
        if (input && input.val() !== null && input.val() !== '') {
            newProps[f] = input.val()
        }
    })

    if (newProps['volume']) newProps['volume'] /= 100 // convert percentage

    splitDimensionsIntoWidthAndHeight(newProps)
    splitPositionIntoXposAndYpos(newProps)

    var type = newProps.type || input.type

    if (!type) {
        showMessage('Please select a type', 'info')
        return
    }

    if (type === 'test_video' && !newProps.pattern) {
        showMessage('Please select a pattern', 'info')
        return
    }

    if (type === 'uri') {
        var uri = newProps.uri || (input.props && input.props.uri)
        good_uri_regexp = '^(file|rtp|rtsp|rtmp|http|https)://'
        if (!uri || !uri.match(good_uri_regexp)) {
            showMessage('uri must start with ' + good_uri_regexp, 'info')
            return
        }
    }

    if (type === 'image') {
        var uri = newProps.uri || (input.props && input.props.uri)
        good_uri_regexp = '^(file||http|https)://'
        if (!uri || !uri.match(good_uri_regexp)) {
            showMessage('Image uri must start with ' + good_uri_regexp, 'info')
            return
        }
    }

    if (type === 'html') {
        var uri = newProps.uri || (input.props && input.props.uri)
        good_uri_regexp = '^(file||http|https)://'
        if (!uri || !uri.match(good_uri_regexp)) {
            showMessage('HTML layer must start with ' + good_uri_regexp, 'info')
            return
        }
    }

    if (!Object.keys(newProps).length) {
        showMessage('No new values', 'info')
        return
    }

    delete newProps.type
    inputsHandler._submitCreateOrEdit(input.id, {type: type, props: newProps})
    hideModal();
}

inputsHandler.delete = function(input) {
    $.ajax({
        contentType: "application/json",
        type: 'DELETE',
        url: 'api/inputs/' + input.id,
        dataType: 'json',
        success: function() {
            showMessage('Successfully deleted input ' + input.id, 'success')
            updatePage()
        },
        error: function() {
            showMessage('Sorry, an error occurred whlst deleting input ' + input.id, 'danger')
        }
    });
    return false
}

inputsHandler._submitCreateOrEdit = function (id, values) {
    const type = (id != null) ? 'POST' : 'PUT'
    const url = (id != null) ? 'api/inputs/' + id : 'api/inputs'
    $.ajax({
        contentType: 'application/json',
        type, url,
        dataType: 'json',
        data: JSON.stringify(values),
        success: function() {
            showMessage('Successfully created or updated an input', 'success')
            updatePage()
        },
        error: function() {
            showMessage('Sorry, an error occurred', 'danger')
        }
    });
}

inputsHandler.setState = function(id, state) {
    return inputsHandler._submitCreateOrEdit(id, {state})
}

inputsHandler.patternTypes = [
    'SMPTE 100% color bars',
    'Random (television snow)',
    '100% Black',
    '100% White',
    'Red',
    'Green',
    'Blue',
    'Checkers 1px',
    'Checkers 2px',
    'Checkers 4px',
    'Checkers 8px',
    'Circular',
    'Blink',
    'SMPTE 75% color bars',
    'Zone plate',
    'Gamut checkers',
    'Chroma zone plate',
    'Solid color',
    'Moving ball',
    'SMPTE 100% color bars',
    'Bar',
    'Pinwheel',
    'Spokes',
    'Gradient',
    'Colors'
]

inputsHandler.waveTypes = [
    'Sine',
    'Square',
    'Saw',
    'Triangle',
    'Silence',
    'White uniform noise',
    'Pink noise',
    'Sine table',
    'Periodic Ticks',
    'White Gaussian noise',
    'Red (brownian) noise',
    'Blue noise',
    'Violet noise'
]

inputsHandler.decklinkModes = [
    'Automatic detection (Hardware Dependant)',
    'NTSC SD 60i',
    'NTSC SD 60i (24 fps)',
    'PAL SD 50i',
    'NTSC SD 60p',
    'PAL SD 50p',
    'HD1080 23.98p',
    'HD1080 24p',
    'HD1080 25p',
    'HD1080 29.97p',
    'HD1080 30p',
    'HD1080 50i',
    'HD1080 59.94i',
    'HD1080 60i',
    'HD1080 50p',
    'HD1080 59.94p',
    'HD1080 60p',
    'HD720 50p',
    'HD720 59.94p',
    'HD720 60p',
    '2k 23.98p',
    '2k 24p',
    '2k 25p',
    '4k 23.98p',
    '4k 24p',
    '4k 25p',
    '4k 29.97p',
    '4k 30p',
    '4k 50p',
    '4k 59.94p',
    '4k 60p',
]

inputsHandler.decklinkConnection = [
    'Auto (Hardware Dependant)',
    'SDI',
    'HDMI',
    'Optical SDI',
    'Component',
    'Composite',
    'S-Video',
]

function prettyDuration(d) {
    if (d < 0) return null
    var seconds = Math.floor(d / 1000000000)
    var minutes = Math.floor(seconds/60)
    var justSeconds = seconds % 60
    return minutes + ':' + (justSeconds < 10 ? '0' : '') + justSeconds
}

inputsHandler.getNextZorder = function() {
    maxZorder = 1
    inputsHandler.items.forEach(i =>{
        if (i.props && i.props.zorder && i.props.zorder >= maxZorder) maxZorder = i.props.zorder + 1
    })
    return maxZorder
}
