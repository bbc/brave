//
// This web interface has been quickly thrown together. It's not production code.
//

overlaysHandler = {}
overlaysHandler.items = []

overlaysHandler.findById = function(id) {
    return overlaysHandler.items.find(function(x) { return x.id == id })
}

overlaysHandler.draw = function() {
    overlaysHandler._drawCards()
}

overlaysHandler.showFormToAdd = function() {
    overlaysHandler._showForm({})
}

overlaysHandler.showFormToEdit = function(overlay) {
    overlaysHandler._showForm(overlay)
}

overlaysHandler._drawCards = () => {
    $('#cards').append(overlaysHandler.items.map(overlaysHandler._asCard))
}

overlaysHandler._asCard = (overlay) => {
    return components.card({
        title: 'Overlay ' + overlay.id + ' (' + prettyType(overlay.type) + ')',
        options: overlaysHandler._optionButtonsForOverlay(overlay),
        body: overlaysHandler._overlayCardBody(overlay),
        mixOptions: overlaysHandler._getMixOptions(overlay)
    })
}

overlaysHandler._optionButtonsForOverlay  = (overlay) => {
    var editButton   = components.editButton().click(() => { overlaysHandler.showFormToEdit(overlay); return false })
    var deleteButton = components.deleteButton().click(() => { overlaysHandler.delete(overlay); return false })
    return [editButton, deleteButton]
}

overlaysHandler._overlayCardBody = (overlay) => {
    const details = []
    if (overlay.effect_name) details.push('<strong>Effect:</strong> ' + overlay.effect_name)
    if (overlay.text) details.push('<strong>Text:</strong> ' + overlay.text)
    if (overlay.valignment) details.push('<strong>Vertical alignment:</strong> ' + overlay.valignment)
    return details.map(d => $('<div></div>').append(d))
}

overlaysHandler.overlay = (overlay) => {
    submitCreateOrEdit('overlay', overlay.id, {visible: true})
}

overlaysHandler.remove = (overlay) => {
    submitCreateOrEdit('overlay', overlay.id, {visible: false})
}

overlaysHandler._getMixOptions = (overlay) => {
    var div = $('<div class="mix-option"></div>')
    if (!overlay.source) {
        div.addClass('mix-option-not-connected')
        return div.append('Not connected')
    }
    var showingOrHidden
    if (overlay.visible) {
        showingOrHidden = 'In mix'
        div.addClass('mix-option-showing')
        var removeButton = components.removeButton()
        removeButton.click(() => { overlaysHandler.remove(overlay); return false })
        var buttons = $('<div class="option-icons"></div>').append(removeButton)
        div.append(buttons)
    }
    else {
        showingOrHidden = 'Not in mix'
        div.addClass('mix-option-hidden')
        var overlayButton = components.overlayButton()
        overlayButton.click(() => { overlaysHandler.overlay(overlay); return false })
        var buttons = $('<div class="option-icons"></div>').append(overlayButton)
        div.append(buttons)
    }
    div.append('<strong>' + prettyUid(overlay.source) + ':</strong> ' + showingOrHidden)
    return div
}

overlaysHandler.delete = function(overlay) {
    $.ajax({
        contentType: "application/json",
        type: 'DELETE',
        url: 'api/overlays/' + overlay.id,
        dataType: 'json',
        success: function() {
            showMessage('Successfully deleted overlay ' + overlay.id)
            updatePage()
        },
        error: function(response) {
            showMessage(response.responseJSON && response.responseJSON.error ?
                'Error deleting overlay: ' + response.responseJSON.error : 'Error deleting overlay')
        }
    });
}

overlaysHandler._handleNewFormType = function(event) {
    overlaysHandler._populateForm({type: event.target.value})
}

overlaysHandler._showForm = function(overlay) {
    overlaysHandler.currentForm = $('<form></form>')
    var label = overlay && overlay.hasOwnProperty('id') ? 'Edit overlay ' + overlay.id : 'Add overlay'
    showModal(label, overlaysHandler.currentForm, overlaysHandler._handleFormSubmit)
    overlaysHandler._populateForm(overlay)
}

overlaysHandler._populateForm = function(overlay) {
    var form = overlaysHandler.currentForm
    form.empty()

    var isNew = !overlay.hasOwnProperty('id')
    if (isNew) {
        options = {
            text: 'Text',
            clock: 'Clock',
            effect: 'Effect'
        }
        form.append(formGroup({
            id: 'overlay-type',
            label: 'Type',
            name: 'type',
            initialOption: 'Select a type...',
            options,
            value: overlay.type
        }))
    }
    else {
        form.append('<input type="hidden" name="id" value="' + overlay.id + '">')
    }

    form.append(getSourceSelect(overlay, isNew))
    if (!overlay.type) {
    }
    else if (overlay.type === 'text' || overlay.type === 'clock') {
        form.append(formGroup({
            id: 'overlay-text',
            label: 'Text',
            name: 'text',
            value: overlay.text || '',
            help: 'The text to be shown by this overlay'
        }))
        form.append(formGroup({
            id: 'overlay-valignment',
            label: 'Vertical alignment',
            name: 'valignment',
            initialOption: 'Select an alignment...',
            options: overlaysHandler.valignmentTypes,
            value: overlay && overlay.valignment ? overlay.valignment : 'bottom'
        }))
    }
    else if (overlay.type === 'effect') {
        form.append(formGroup({
            id: 'overlay-effect',
            label: 'Effect',
            name: 'effect_name',
            initialOption: 'Select an effect...',
            options: overlaysHandler.effectNames,
            value: overlay ? overlay.effect_name : undefined
        }))
    }

    form.find('select[name="type"]').change(overlaysHandler._handleNewFormType);
}

overlaysHandler._handleNewFormType = function(event) {
    overlaysHandler._showForm({type: event.target.value})
}

overlaysHandler._handleFormSubmit = function() {
    var form = overlaysHandler.currentForm
    var idField = form.find('input[name="id"]')
    var id = idField.length ? idField.val() : null
    var overlay = (id != null) ? overlaysHandler.findById(id) : {}
    var newProps = {}

    const fields = ['type', 'text', 'valignment', 'effect_name', 'source']
    fields.forEach(f => {
        var overlay = form.find('[name="' + f + '"]')
        if (overlay && overlay.val() != null) {
            newProps[f] = overlay.val()
        }
    })

    var type = newProps.type || overlay.type

    if (!type) {
        showMessage('Please select a type')
        return
    }

    if ((type === 'text' || type == 'clock') && !newProps.valignment) {
        showMessage('Please select a vertical alignment')
        return
    }

    if ((type === 'effect') && !newProps.effect_name) {
        showMessage('Please select an effect')
        return
    }

    if (!Object.keys(newProps).length) {
        showMessage('No new values')
        return
    }

    if (newProps.source === 'none') newProps.source = null
    submitCreateOrEdit('overlay', id, newProps)
    hideModal();
}

overlaysHandler.valignmentTypes = {
    top: 'Top',
    center: 'Center',
    bottom: 'Bottom',
    baseline: 'Baseline'
}

overlaysHandler.effectNames = {
    'agingtv': 'AgingTV (adds age to video input using scratches and dust)',
    'burn': 'Burn (adjusts the colors in the video)',
    'chromium': 'Chromium (breaks the colors of the video)',
    'dicetv': 'DiceTV (\'Dices\' the screen up into many small squares)',
    'dilate': 'Dilate (copies the brightest pixel around)',
    'dodge': 'Dodge (saturates the colors in the video)',
    'edgetv': 'EdgeTV effect',
    'exclusion': 'Exclusion (exclodes the colors in the video)',
    'optv': 'OpTV (Optical art meets real-time video)',
    'radioactv': 'RadioacTV (motion-enlightment)',
    'revtv': 'RevTV (A video waveform monitor for each line of video)',
    'rippletv': 'RippleTV (ripple mark effect on the video)',
    'solarize': 'Solarize (tunable inverse in the video)',
    'streaktv': 'StreakTV (makes after images of moving objects)',
    'vertigotv': 'VertigoTV (blending effector with rotating and scaling)',
    'warptv': 'WarpTV (goo\'ing of the video)',
}
