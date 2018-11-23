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
        title: 'Input ' + input.id + ' (' + prettyType(input.type) + ')',
        options: inputsHandler._optionButtonsForInput(input),
        body: inputsHandler._inputCardBody(input),
        state: components.stateBox(input, inputsHandler.setState),
        mixOptions: inputsHandler._getMixOptions(input)
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

    if (input.hasOwnProperty('duration')) {
        var duration = prettyDuration(input.duration)
        if (duration !== null) details.push('<strong>duration:</strong> ' + duration)
    }

    if (input.hasOwnProperty('error_message')) details.push('<strong>ERROR:</strong> <span style="color:red">' + input.error_message + '</span>')
    return details.map(d => $('<div></div>').append(d))
}

inputsHandler._getMixOptions = (input) => {
    return mixersHandler.items.map(mixer => {
        if (!mixer.sources) return
        var foundThisInput = mixer.sources.find(i => i.id === input.id && i.type === 'input')
        var inMix = foundThisInput && foundThisInput.in_mix ? 'In mix' : 'Not in mix'
        var div = $('<div class="mix-option"></div>')
        if (foundThisInput && foundThisInput.in_mix) {
            div.addClass('mix-option-showing')
            var removeButton = components.removeButton()
            removeButton.click(() => { mixersHandler.remove(mixer, input); return false })
            var buttons = $('<div class="option-icons"></div>')
            buttons.append([removeButton])
            div.append(buttons)
        }
        else {
            div.addClass('mix-option-hidden')
            var cutButton = components.cutButton()
            cutButton.click(() => { mixersHandler.cut(mixer, input); return false })
            var overlayButton = components.overlayButton()
            overlayButton.click(() => { mixersHandler.overlay(mixer, input); return false })
            var buttons = $('<div class="option-icons"></div>')
            buttons.append([cutButton, overlayButton])
            div.append(buttons)
        }
        div.append('<strong>Mixer ' + mixer.id + ':</strong> ' + inMix)
        return div
    }).filter(x => !!x)
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

    var isNew = !input.hasOwnProperty('id')
    if (isNew) {
        var options = {
            'uri': 'URI (for files, RTMP, RTSP and HLS)',
            'image': 'Image',
            'html': 'HTML (for showing a web page)',
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
