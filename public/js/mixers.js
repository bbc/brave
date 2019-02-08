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
    submitCreateOrEdit('mixer', id, {state})
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
        state: components.stateBox(mixer, mixersHandler.setState),
        mixOptions: components.getMixOptions(mixer)
    })
}

mixersHandler._optionButtonsForMixer = (mixer) => {
    const editButton = components.editButton().click(() => { mixersHandler.showFormToEdit(mixer); return false })
    const deleteButton = components.deleteButton().click(() => { mixersHandler.delete(mixer); return false })
    return [editButton, deleteButton]
}

mixersHandler._mixerCardBody = (mixer) => {
    var details = []
    if (mixer.hasOwnProperty('pattern')) details.push('<div><strong>Background:</strong> ' + inputsHandler.patternTypes[mixer.pattern] + '</div>')
    if (mixer.hasOwnProperty('width') &&
        mixer.hasOwnProperty('height')) details.push('<div><strong>Dimension:</strong> ' + prettyDimensions(mixer) + '</div>')
    return details
}

mixersHandler._sendMixerCommand = function(mixer, source, command) {
    $.ajax({
        type: 'POST',
        url: 'api/mixers/' + mixer.id + '/' + command,
        dataType: 'json',
        data: JSON.stringify({uid:source.uid}),
        success: function() {
            showMessage('Success in ' + command + ' for ' + source.uid + ' to ' + mixer.uid)
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

    if (mixer.hasOwnProperty('id')) {
        form.append('<input type="hidden" name="id" value="' + mixer.id + '">')
    }

    form.append(getDimensionsSelect('dimensions', mixer.width, mixer.height))

    form.append(formGroup({
        id: 'mixer-pattern',
        label: 'Pattern',
        name: 'pattern',
        options: inputsHandler.patternTypes,
        initialOption: 'Select a pattern...',
        value: mixer.pattern
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
    submitCreateOrEdit('mixer', id, newProps)
    hideModal();
}

mixersHandler.create = () => {
    submitCreateOrEdit('mixer', null, {})
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
