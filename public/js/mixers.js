//
// This web interface has been quickly thrown together. It's not production code.
//

mixersHandler = {}
mixersHandler.items = []

mixersHandler.findById = function(id) {
    return mixersHandler.items.find(function(x) { return x.id == id })
}

mixersHandler.showFormToEdit = function(mixer) {
    mixersHandler._showForm(mixer)
}

mixersHandler.draw = function() {
    mixersHandler._drawCards()
}

mixersHandler.setState = function(id, state) {
    return mixersHandler._submitCreateOrEdit(id, {state})
}

mixersHandler.remove = (mixer, source) => {
    mixersHandler._sendMixerCommand(mixer, source, 'remove_source')
}

mixersHandler.cut = (mixer, source) => {
    mixersHandler._sendMixerCommand(mixer, source, 'cut_to_source')
}

mixersHandler.overlay = (mixer, source) => {
    mixersHandler._sendMixerCommand(mixer, source, 'overlay_source')
}

mixersHandler._drawCards = () => {
    $('#cards').append(mixersHandler.items.map(mixersHandler._asCard))
}

mixersHandler._asCard = (mixer) => {
    return components.card({
        title: 'Mixer ' + mixer.id,
        options: mixersHandler._optionButtonsForMixer(mixer),
        body: mixersHandler._mixerCardBody(mixer),
        state: components.stateBox(mixer, mixersHandler.setState)
    })
}

mixersHandler._optionButtonsForMixer = (mixer) => {
    const editButton = components.editButton().click(() => { mixersHandler.showFormToEdit(mixer); return false })
    const deleteButton = components.deleteButton().click(() => { mixersHandler.delete(mixer); return false })
    return [editButton, deleteButton]
}

mixersHandler._mixerCardBody = (mixer) => {
    var details = []
    if (mixer.props.hasOwnProperty('pattern')) details.push('<div><strong>Background:</strong> ' + inputsHandler.patternTypes[mixer.props.pattern] + '</div>')
    if (mixer.props.hasOwnProperty('width') &&
        mixer.props.hasOwnProperty('height')) details.push('<div><strong>Dimension:</strong> ' + prettyDimensions(mixer.props) + '</div>')
    return details
}

mixersHandler._sendMixerCommand = function(mixer, source, command) {
    $.ajax({
        type: 'POST',
        url: 'api/mixers/' + mixer.id + '/' + command,
        dataType: 'json',
        data: JSON.stringify({type: 'input', id: source.id}),
        success: function() {
            showMessage('Success in ' + command + ' for input ' + source.id + ' to mixer ' + mixer.id)
            updatePage()
        },
        error: function() {
            showMessage('Sorry, an error occurred')
        }
    });
}

mixersHandler._showForm = function(mixer) {
    mixersHandler.currentForm = $('<form></form>')
    var label = mixer && mixer.hasOwnProperty('id') ? 'Edit mixer ' + mixer.id : 'Add mixer'
    showModal(label, mixersHandler.currentForm, mixersHandler._handleFormSubmit)
    mixersHandler._populateForm(mixer)
}

mixersHandler._populateForm = function(mixer) {
    var form = mixersHandler.currentForm
    form.empty()

    if (!mixer.props) mixer.props = {}

    if (mixer.hasOwnProperty('id')) {
        form.append('<input type="hidden" name="id" value="' + mixer.id + '">')
    }

    form.append(getDimensionsSelect('dimensions', mixer.props.width, mixer.props.height))

    form.append(formGroup({
        id: 'mixer-pattern',
        label: 'Pattern',
        name: 'pattern',
        options: inputsHandler.patternTypes,
        initialOption: 'Select a pattern...',
        value: mixer.props.pattern
    }))
}

mixersHandler._handleFormSubmit = function() {
    var form = mixersHandler.currentForm
    var idField = form.find('input[name="id"]')
    var id = idField.length ? idField.val() : null
    var mixer = (id != null) ? mixersHandler.findById(id) : {}
    var newProps = {}

    fields = ['pattern', 'dimensions']
    fields.forEach(function(f) {
        var mixer = form.find('[name="' + f + '"]')
        if (mixer && mixer.val() != null) {
            newProps[f] = mixer.val()
        }
    })
    splitDimensionsIntoWidthAndHeight(newProps)
    console.log('Submitting new mixer with values', newProps)
    mixersHandler._submitCreateOrEdit(id, {props: newProps})
    hideModal();
}

mixersHandler.create = () => {
    mixersHandler._submitCreateOrEdit(null, {})
}


mixersHandler._submitCreateOrEdit = function (id, values) {
    var putOrPost = (id != null) ? 'POST' : 'PUT'
    var url = (id != null) ? 'api/mixers/' + id : 'api/mixers'
    $.ajax({
        contentType: 'application/json',
        type: putOrPost,
        url: url,
        dataType: 'json',
        data: JSON.stringify(values),
        success: function() {
            showMessage('Successfully created/updated mixer', 'success')
            updatePage()
        },
        error: function(response) {
            showMessage(response.responseJSON && response.responseJSON.error ?
                'Error updating mixer: ' + response.responseJSON.error : 'Error updating mixer')
        }
    });
}

mixersHandler.delete = function(mixer) {
    $.ajax({
        contentType: "application/json",
        type: 'DELETE',
        url: 'api/mixers/' + mixer.id,
        dataType: 'json',
        success: function() {
            showMessage('Successfully deleted mixer ' + mixer.id, 'success')
            updatePage()
        },
        error: function() {
            showMessage('Sorry, an error occurred whlst deleting mixer ' + mixer.id, 'danger')
        }
    });
    return false
}
