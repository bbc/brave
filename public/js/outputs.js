//
// This web interface has been quickly thrown together. It's not production code.
//

outputsHandler = {}

outputsHandler.findById = (id) => {
    return outputsHandler.items.find(i => i.id == id)
}
outputsHandler.findByDetails = (details) => {
    return outputsHandler.items.find(i => {
        if (details.type && details.type !== i.type) return false
        if (details.hasOwnProperty('source') && details.source !== i.source) return false
        return true
    })
}

outputsHandler.draw = function() {
    if (!outputsHandler.items) outputsHandler.items = []
    outputsHandler._drawCards()
    preview.handleOutputsUpdate()
}

outputsHandler.showFormToAdd = function() {
    outputsHandler._showForm({})
}

outputsHandler.showFormToEdit = function(overlay) {
    outputsHandler._showForm(overlay)
}

outputsHandler._drawCards = () => {
    $('#cards').append(outputsHandler.items.map(outputsHandler._asCard))
}

outputsHandler._asCard = (output) => {
    var title = 'Output ' + (!output.uid.includes("output") ? output.uid : output.id); 
    return components.card({
        title: title + ' (' + prettyType(output.type) + ')',
        options: outputsHandler._optionButtonsForOutput(output),
        body: outputsHandler._outputCardBody(output),
        state: components.stateBox(output, outputsHandler.setState),
    })
}

outputsHandler._optionButtonsForOutput = (output) => {
    const editButton = components.editButton().click(() => { outputsHandler.showFormToEdit(output); return false })
    const deleteButton = components.deleteButton().click(() => { outputsHandler.delete(output); return false })
    return [editButton, deleteButton]
}

outputsHandler._outputCardBody = (output) => {
    var details = []
    if (output.current_num_peers) {
        details.push('<strong>Number of connections:</strong> ' + output.current_num_peers)
    }
    if (output.location) {
        details.push('<strong>Location:</strong> ' + output.location)
    }
    else if (output.uri) {
        details.push('<strong>URI:</strong> <code>' + output.uri + '</code></div>')
    }
    else if (output.host && output.port && output.type === 'tcp') {
        current_domain = $('<a>').attr('href', document.location.href).prop('hostname');
        host = current_domain === '127.0.0.1' ? output.host : current_domain
        // Instead of domain we can use output.host but it may be an internal (private) IP
        details.push('<strong>URI:</strong> <code>tcp://' + host + ':' + output.port + '</code> (Use VLC to watch this)')
        details.push('<strong>Container:</strong> <code>' + output.container + '</code>')
    }

    if (output.hasOwnProperty('width') &&
        output.hasOwnProperty('height')) details.push('<strong>Output size:</strong> ' + prettyDimensions(output))

    if (output.audio_bitrate) {
        details.push('<strong>Audio bitrate:</strong> ' + output.audio_bitrate)
    }

    if (output.hasOwnProperty('stream_name')) {
        details.push('<strong>Stream name:</strong> ' + output.stream_name)
    }

    if (output.hasOwnProperty('source')) {
        details.push('<strong>Source:</strong> ' + output.source)
    }
    else {
        details.push('<strong>Source:</strong> None')
    }

    if (output.hasOwnProperty('error_message')) details.push('<strong>ERROR:</strong> <span style="color:red">' + output.error_message + '</span>')

    return details.map(d => $('<div></div>').append(d))
}

outputsHandler.requestNewOutput = function(args) {
    submitCreateOrEdit('output', null, args)
}

function getVideoElement() {
    return document.getElementById('stream');
}

outputsHandler.delete = function(output) {
    $.ajax({
        contentType: "application/json",
        type: 'DELETE',
        url: 'api/outputs/' + output.id,
        dataType: 'json',
        success: function() {
            showMessage('Successfully deleted output ' + output.id, 'success')
            updatePage()
        },
        error: function() {
            showMessage('Sorry, an error occurred whilst deleting output ' + output.id, 'warning')
        }
    });
}

outputsHandler._handleNewFormType = function(event) {
    outputsHandler._populateForm({type: event.target.value})
}

outputsHandler._showForm = function(output) {
    outputsHandler.currentForm = $('<form></form>')
    var label = output && output.hasOwnProperty('id') ? 'Edit output ' + output.id : 'Add output'
    showModal(label, outputsHandler.currentForm, outputsHandler._handleFormSubmit)
    outputsHandler._populateForm(output)
}

outputsHandler._populateForm = function(output) {
    var form = outputsHandler.currentForm
    form.empty()
    var isNew = !output.hasOwnProperty('id')
    if (isNew) {
        form.append(outputsHandler._getOutputsSelect(output))
    }
    else {
        form.append('<input type="hidden" name="id" value="' + output.id + '">')
    }
    form.append(getSourceSelect(output, isNew))
    if (!output.type) {
    }
    else if (output.type === 'local') {
        form.append('<div>(There are no extra settings for local outputs.)</div>');
    }
    else if (output.type === 'tcp') {
        form.append(formGroup({
            id: 'output-container',
            label: 'Container',
            name: 'container',
            options: {mpeg: 'MPEG', ogg: 'OGG'},
            value: (output.type || 'mpeg')
        }))

        form.append(formGroup({
            id: 'input-audio_bitrate',
            label: 'Audio bitrate',
            name: 'audio_bitrate',
            type: 'number',
            value: output.audio_bitrate || '',
            help: 'Leave blank for default (128000)',
            min: 1000,
            step: 1000,
            max: 128000*16
        }))

        form.append(getDimensionsSelect('dimensions', output.width, output.height))
    }
    else if (output.type === 'rtmp') {
        form.append(formGroup({
            id: 'output-uri',
            label: 'Location (URI)',
            name: 'uri',
            type: 'text',
            value: output.uri || '',
            help: 'Example: <code>rtmp://184.72.239.149/vod/BigBuckBunny_115k.mov</code>',
        }));
    }
    else if (output.type === 'file') {
        form.append(formGroup({
            id: 'output-location',
            label: 'Location (filename)',
            name: 'location',
            type: 'text',
            value: output.location || '',
            help: 'Example: <code>/tmp/foo.mp4</code>',
        }));
    }
    else if (output.type === 'kvs') {
        form.append(formGroup({
            id: 'output-stream-name',
            label: 'Stream name',
            name: 'stream_name',
            type: 'text',
            value: output.location || '',
            help: 'You can create one on the <a href="https://us-west-2.console.aws.amazon.com/kinesisvideo/streams">AWS KVS console</a>',
        }));
    }

    form.find('select[name="type"]').change(outputsHandler._handleNewFormType);
}

outputsHandler._getOutputsSelect = function(output) {
    var options = {
        'tcp'  : 'TCP (server)',
        'rtmp' : 'RTMP (send to remote server)',
        'image' : 'JPEG image every 1 second',
        'file' : 'File (Write audio/video to a local file)',
        'webrtc' : 'WebRTC for web preview',
        'kvs' : 'AWS Kinesis Video',
        'local': 'Local (pop-up audio/video on this server, for debugging)',
    }
    return formGroup({
        id: 'output-type',
        label: 'Type',
        name: 'type',
        initialOption: 'Select a type...',
        options,
        value: output.type
    })
}

outputsHandler._handleNewFormType = function(event) {
    outputsHandler._populateForm({type: event.target.value})
}

outputsHandler._handleFormSubmit = function() {
    var form = outputsHandler.currentForm
    var idField = form.find('input[name="id"]')
    var id = idField.length ? idField.val() : null
    var output = (id != null) ? outputsHandler.findById(id) : {}
    var newProps = {}

    const fields = ['type', 'uri', 'host', 'port', 'container', 'location',
                    'audio_bitrate', 'dimensions', 'source', 'stream_name']
    fields.forEach(f => {
        var input = form.find('[name="' + f + '"]')
        if (input && input.val() != null) newProps[f] = input.val()
    })

    if (newProps.audio_bitrate === '') newProps.audio_bitrate = null

    splitDimensionsIntoWidthAndHeight(newProps)

    var type = newProps.type || output.type

    if (!type) {
        showMessage('Please select a type')
        return
    }

    const VALID_TYPES = ['local', 'tcp', 'image', 'file', 'webrtc', 'kvs', 'rtmp']
    if (VALID_TYPES.indexOf(type) === -1) {
        showMessage('Invalid type ' + type)
        return
    }

    if (type === 'rtmp') {
        good_uri_regexp = '^rtmp(s?)://'
        if (!newProps.uri || !newProps.uri.match(good_uri_regexp)) {
            showMessage('uri must start with ' + good_uri_regexp)
            return
        }
    }

    if (!Object.keys(newProps).length) {
        showMessage('No new values')
        return
    }

    if (newProps.source === 'none') newProps.source = null
    submitCreateOrEdit('output', output.id, newProps)
    hideModal();
}

outputsHandler.setState = function(id, state) {
    submitCreateOrEdit('output', id, {state})
}
