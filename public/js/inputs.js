//
// This web interface has been quickly thrown together. It's not production code.
//
inputsHandler = {}
inputsHandler.items = []
const GstSecond = 1000000000

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
    var end = input.duration/GstSecond
    secondsSeek = prompt("What should input " + input.id + "seek to, in seconds. (0=start, " + end + "=end)");
    inputsHandler._submitCreateOrEdit(input.id, {position:secondsSeek*GstSecond})
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
    if (input.uri) details.push('<div><code>' + input.uri + '</code></div>')
    if (input.hasOwnProperty('width') &&
        input.hasOwnProperty('height')) details.push('<strong>Input size:</strong> ' + prettyDimensions(input))
    if (input.hasOwnProperty('width') &&
        input.hasOwnProperty('height')) details.push('<div><strong>Resized to:</strong> ' + prettyDimensions(input) + '</div>')
    if (input.hasOwnProperty('framerate')) details.push('<div><strong>Framerate:</strong> ' + Math.round(input.framerate) + '</div>')
    if (input.hasOwnProperty('xpos') && input.hasOwnProperty('ypos')) details.push('<div><strong>Position on screen:</strong> ' + input.xpos + 'x' + input.ypos + '</div>')
    if (input.hasOwnProperty('zorder')) details.push('<strong>Z-order:</strong> ' + input.zorder)
    if (input.hasOwnProperty('audio_channels')) details.push('<div><strong>Audio channels:</strong> ' + input.audio_channels + '</div>')
    if (input.hasOwnProperty('audio_rate')) details.push('<div><strong>Audio rate:</strong> ' + input.audio_rate + '</div>')
    if (input.hasOwnProperty('volume')) details.push('<div><strong>Volume:</strong> ' + (100 * input.volume) + '&#37;</div>')
    if (input.hasOwnProperty('loop')) details.push('<div><strong>Loop:</strong> ' + (input.loop ? 'Yes' : 'No') + '</div>')
    if (input.hasOwnProperty('input_volume')) details.push('<div><strong>Input volume:</strong> ' + input.input_volume + '</div>')
    if (input.hasOwnProperty('freq')) details.push('<div><strong>Frequency:</strong> ' + input.freq + 'Hz</div>')
    if (input.hasOwnProperty('pattern')) details.push('<div><strong>Pattern:</strong> ' + inputsHandler.patternTypes[input.pattern] + '</div>')
    if (input.hasOwnProperty('wave')) details.push('<div><strong>Wave:</strong> ' + inputsHandler.waveTypes[input.wave] + '</div>')
    if (input.hasOwnProperty('device')) details.push('<div><strong>Device Num:</strong> ' + input.device + '</div>')
    if (input.hasOwnProperty('connection')) details.push('<div><strong>Connection Type:</strong> ' + inputsHandler.decklinkConnection[input.connection] + '</div>')
    if (input.hasOwnProperty('mode')) details.push('<div><strong>Input Mode:</strong> ' + inputsHandler.decklinkModes[input.mode] + '</div>')

    if (input.hasOwnProperty('duration')) {
        var duration = prettyDuration(input.duration)
        if (duration !== null) details.push('<strong>Duration:</strong> ' + duration)
    }

    if (input.hasOwnProperty('buffer_duration')) {
        var duration = prettyDuration(input.buffer_duration)
        if (duration !== null) details.push('<strong>Buffer duration:</strong> ' + duration)
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
        value: (input.xpos || 0) + 'x' + (input.ypos || 0),
        help: 'In the format <samp>&lt;width&gt;x&lt;height&gt;</samp>. The default, <samp>0x0</samp>, puts it in the top-left corner.'
    })

    const loopBox = formGroup({
        id: 'input-loop',
        type: 'checkbox',
        name: 'loop',
        label: 'Loop (content replays once finished)',
        value: input.loop
    })

    const bufferDuationBox = formGroup({
        id: 'input-buffer-duration',
        label: 'Buffer duaration (seconds)',
        name: 'buffer_duration',
        type: 'number',
        value: input.buffer_duration / GstSecond,
        help: 'Amount to buffer input, in seconds. Leave blank for default.'
    })

    var zOrderBox = formGroup({
        id: 'input-zorder',
        label: 'Z-order',
        name: 'zorder',
        type: 'number',
        value: input.zorder || inputsHandler.getNextZorder()
    })

    var uriRow = formGroup({
        id: 'input-uri',
        label: 'Location (URI)',
        name: 'uri',
        type: 'text',
        value: input.uri || '',
        help: uriExamples,
    })

    const sizeBox = getDimensionsSelect('dimensions', input.width, input.height)

    var patternBox = formGroup({
        id: 'input-pattern',
        label: 'Pattern',
        name: 'pattern',
        options: inputsHandler.patternTypes,
        initialOption: 'Select a pattern...',
        value: input.pattern || inputsHandler.patternTypes[0]
    })

    var waveBox = formGroup({
        id: 'input-wave',
        label: 'Waveform',
        name: 'wave',
        options: inputsHandler.waveTypes,
        initialOption: 'Select a wave...',
        value: input.wave || inputsHandler.waveTypes[0]
    })

    var freqBox = formGroup({
        id: 'input-freq',
        label: 'Frequency (Hz)',
        name: 'freq',
        type: 'number',
        value: input.freq || 440,
        min: 20,
        step: 100,
        max: 20000
    })

    var device = formGroup({
        id: 'input-device',
        label: 'Device Num',
        name: 'device',
        type: 'number',
        value: input.device || 0
    })

    var connection = formGroup({
        id: 'connection-device',
        label: 'Connection Type',
        name: 'connection',
        type: 'number',
        options: inputsHandler.decklinkConnection,
        initialOption: 'Select connection type',
        value: input.connection || inputsHandler.decklinkConnection[1]
    })

    var mode = formGroup({
        id: 'mode-device',
        label: 'Input Mode',
        name: 'mode',
        type: 'number',
        options: inputsHandler.decklinkModes,
        initialOption: 'Select input mode',
        value: input.mode || inputsHandler.decklinkModes[17]
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
        form.append(components.volumeInput(input.volume));
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
        form.append(loopBox);
        form.append(positionBox);
        form.append(sizeBox);
        form.append(zOrderBox);
        form.append(components.volumeInput(input.volume));
        form.append(bufferDuationBox)
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
    const isNew = id == null
    const input = isNew ? {} : inputsHandler.findById(id)
    const newProps = {}

    fields = ['type', 'uri', 'position', 'zorder', 'dimensions', 'freq', 'volume', 'input_volume', 'pattern', 'wave', 'buffer_duration']
    fields.forEach(function(f) {
        var input = form.find('[name="' + f + '"]')
        if (input && input.val() !== null && input.val() !== '') {
            newProps[f] = input.val()
        }
    })

    const loop_entry = form.find('[name="loop"]')
    if (loop_entry) newProps.loop = loop_entry.is(":checked")

    if (newProps.volume) newProps.volume /= 100 // convert percentage
    if (newProps.buffer_duration) newProps.buffer_duration *= GstSecond

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

    const GOOD_URI_REGEXP = {
        'uri': '^(file|rtp|rtsp|rtmp|http|https)://',
        'image': '^(file||http|https)://',
        'html': '^(file||http|https)://'
    }

    if (GOOD_URI_REGEXP[type]) {
        if (newProps.uri) {
            if (!newProps.uri.match(GOOD_URI_REGEXP[type])) {
                showMessage('uri must start with ' + GOOD_URI_REGEXP, 'info')
            }
        }
        else if (isNew) {
            showMessage('URI field is required', 'info')
        }
    }

    if (!Object.keys(newProps).length) {
        showMessage('No new values', 'info')
        return
    }

    inputsHandler._submitCreateOrEdit(id, newProps)
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
    var seconds = Math.floor(d / GstSecond)
    var minutes = Math.floor(seconds/60)
    var justSeconds = seconds % 60
    return minutes + ':' + (justSeconds < 10 ? '0' : '') + justSeconds
}

inputsHandler.getNextZorder = function() {
    maxZorder = 1
    inputsHandler.items.forEach(i =>{
        if (i.zorder && i.zorder >= maxZorder) maxZorder = i.zorder + 1
    })
    return maxZorder
}
