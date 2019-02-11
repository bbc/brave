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
    submitCreateOrEdit('input', input.id, {position:secondsSeek*GstSecond})
}

inputsHandler._drawCards = () => {
    $('#cards').append(inputsHandler.items.map(inputsHandler._asCard))
}

inputsHandler._asCard = (input) => {
    return components.card({
        uid: input.uid,
        title: prettyUid(input.uid) + ' (' + prettyType(input.type) + ')',
        // options: inputsHandler._optionButtonsForInput(input),
        // body: inputsHandler.detailsDiv(input),
        state: components.stateBox(input, inputsHandler.setState),
        mixOptions: components.getMixOptions(input)
    })
}

// inputsHandler._optionButtonsForInput = (input) => {
//     const buttons = []
//     buttons.push(components.editButton().click(() => { inputsHandler.showFormToEdit(input); return false }))
//     buttons.push(components.deleteButton().click(() => { inputsHandler.delete(input); return false }))
//     if (input.type === 'uri') {
//         buttons.push(components.seekButton().click(() => { inputsHandler.seek(input); return false }))
//     }
//     return buttons
// }

inputsHandler.detailsForTable = (input) => {
    const fields = []
    if (input.hasOwnProperty('audio_channels')) fields.push(['Audio channels', input.audio_channels])
    if (input.hasOwnProperty('audio_rate')) fields.push(['Audio rate', input.audio_rate])
    if (input.hasOwnProperty('host')) fields.push(['Host', input.host])
    if (input.hasOwnProperty('port')) fields.push(['Port', input.port])
    if (input.hasOwnProperty('containers')) fields.push(['Container', container])
    if (input.hasOwnProperty('width') &&
        input.hasOwnProperty('height')) fields.push(['Input size', prettyDimensions(input)])
    if (input.hasOwnProperty('framerate')) fields.push(['Framerate', Math.round(input.framerate)])
    if (input.hasOwnProperty('uri')) fields.push(['uri', $('<code />').append(input.uri)])
    if (input.hasOwnProperty('pattern')) {
        const onChange = val => submitCreateOrEdit('input', input.id, {pattern: val})
        fields.push(['Pattern', getSelect('pattern', input.pattern, 'Select pattern...', inputsHandler.patternTypes, false, onChange)])
    }
    if (input.hasOwnProperty('volume')) {
        const onChange = val => submitCreateOrEdit('input', input.id, {volume: val/100})
        fields.push(['Volume', components.slider(input.volume*100, onChange, {id: 'volume-slider', text_end: '%', min: 0, max: 100, step: 5})])
    }
    if (input.hasOwnProperty('freq')) {
        const onChange = val => submitCreateOrEdit('input', input.id, {freq: val})
        fields.push(['Frequency', components.slider(input.freq, onChange, {id: 'freq-slider', text_end: ' KHz', min: 0, max: 4000, step: 20})])
    }
    if (input.hasOwnProperty('wave')) {
        const onChange = val => submitCreateOrEdit('input', input.id, {wave: val})
        fields.push(['Wave', getSelect('wave', input.wave, 'Select wave...', inputsHandler.waveTypes, false, onChange)])
    }
    if (input.hasOwnProperty('position') && input.position !== null) {
        let position = prettyDuration(input.position)
        if (input.type === 'uri') {
            position = $('<span />').text(position + ' ' ).append(components.seekButton().click(() => {
                inputsHandler.seek(input); return false
            }))
        }
        fields.push(['Position', position])
    }
    if (input.hasOwnProperty('duration') && input.duration !== null) {
        fields.push(['Duration', prettyDuration(input.duration)])
    }
    if (input.hasOwnProperty('buffer_duration') && input.duration !== null) {
        fields.push(['Buffer duration', prettyDuration(input.buffer_duration)])
    }
    if (input.hasOwnProperty('loop')) {
        fields.push(['Loop?', input.loop ? 'Yes' : 'No'])
    }

    if (input.hasOwnProperty('device')) fields.push(['Device num', input.device])
    if (input.hasOwnProperty('connection')) fields.push(['Connection type', inputsHandler.decklinkConnection[input.connection]])
    if (input.hasOwnProperty('mode')) fields.push(['Input mode', inputsHandler.decklinkModes[input.mode]])
    if (input.error_message) fields.push(['ERROR', $('<span style="color:red">' + input.error_message + '</span>')])

    return fields
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

    const hostBox = formGroup({
        id: 'input-host',
        label: 'Hostname',
        name: 'host',
        type: 'text',
        value: input.host || '0.0.0.0'
    })

    const portBox = formGroup({
        id: 'input-port',
        label: 'Port',
        name: 'port',
        type: 'number',
        value: input.port
    })

    const containerBox = formGroup({
        id: 'input-container',
        label: 'Container',
        name: 'container',
        options: {mpeg: 'MPEG', ogg: 'OGG'},
        value: (input.container || 'mpeg')
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
            'tcp_client': 'TCP Client (receive from a TCP server)',
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
        form.append(sizeBox);
    }
    else if (input.type === 'image') {
        if (isNew) form.append(uriRow);
        form.append(sizeBox);
    }
    else if (input.type === 'uri') {
        if (isNew) form.append(uriRow);
        form.append(loopBox);
        form.append(sizeBox);
        form.append(components.volumeInput(input.volume));
        form.append(bufferDuationBox)
    }
    else if (input.type === 'html') {
        if (isNew) form.append(uriRow);
        form.append(sizeBox);
    }
    else if (input.type === 'decklink') {
        if (isNew) form.append(device);
        if (isNew) form.append(mode);
        if (isNew) form.append(connection);
        form.append(sizeBox);
    }
    else if (input.type === 'tcp_client') {
        if (isNew) form.append(hostBox)
        if (isNew) form.append(portBox)
        if (isNew) form.append(containerBox)
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

    fields = ['type', 'uri', 'position', 'dimensions', 'freq', 'volume', 'input_volume', 'pattern', 'wave', 'buffer_duration', 'host', 'port', 'container']
    fields.forEach(function(f) {
        var input = form.find('[name="' + f + '"]')
        if (input && input.val() !== null && input.val() !== '') {
            newProps[f] = input.val()
        }
    })

    const loopEntry = form.find('[name="loop"]')
    if (loopEntry && loopEntry.length > 0) newProps.loop = loopEntry.is(":checked")

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

    submitCreateOrEdit('input', id, newProps)
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

inputsHandler.setState = function(id, state) {
    return submitCreateOrEdit('input', id, {state})
}

inputsHandler.getMixOptions = (input) => {
    return components.getMixOptions(input)
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
