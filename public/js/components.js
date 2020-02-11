//
// This web interface has been quickly thrown together. It's not production code.
//

components = {}

components.editButton = () => {
    return $("<a href=\"#\" class=\"fas fa-edit\" title=\"Edit\"></a>")
}

components.deleteButton = () => {
    return $("<a href=\"#\" class=\"fas fa-trash-alt\" title=\"Delete\"></a>")
}

components.seekButton = () => {
    return $("<a href=\"#\" class=\"fas fa-arrows-alt-h\" title=\"Seek\"></a>")
}

components.seekButton = () => {
    return $("<a href=\"#\" class=\"fas fa-arrows-alt-h\" title=\"Seek\"></a>")
}

components.cutButton = () => {
    return $("<a href=\"#\" class=\"fas fa-cut\" title=\"Cut\"></a>")
}

components.overlayButton = () => {
    return $("<a href=\"#\" class=\"fas fa-layer-group\" title=\"Overlay\"></a>")
}

components.removeButton = () => {
    return $("<a href=\"#\" class=\"fas fa-eye-slash\" title=\"Remove from mix\"></a>")
}

components.mutedButton = () => {
    return $("<a href=\"#\" class=\"fas fa-volume-off\" title=\"Unmute\"></a>")
}

components.unmutedButton = () => {
    return $("<a href=\"#\" class=\"fas fa-volume-up\" title=\"Mute\"></a>")
}

components.stateIcon = (state, currentState) => {
    var selected = state == currentState
    var icons = {
        'PLAYING': 'fa-play',
        'PAUSED': 'fa-pause',
        'READY': 'fa-stop',
        'NULL': 'fa-exclamation-triangle'
    }
    var iconName = icons[state]
    return '<a href=\"#\" class="fas ' + iconName + (selected ? '' : ' icon-unselected') + '" data-state="' + state + '" ></a>'
}

components.openCards = {}
components.card = (block) => {
    var card = $('<div class="block-card"></div>')
    var header = $('<div class="block-card-head"></div>')
    if (block.title) header.append(block.title)
    if (block.options) {
        var options = $('<div class="option-icons"></div>')
        options.append(block.options)
        header.append(options)
    }
    card.append(header)
    if (block.state) card.append(block.state)
    if (block.mixOptions) card.append(block.mixOptions)

    const cardBody = $('<div class="block-card-body"></div>')
    cardBody.append(block.body)
    if (!components.openCards[block.title]) cardBody.css('display', 'none')

    const setToggleMsg = (target) => { target.html(components.openCards[block.title] ? components.hideDetails() : components.showDetails()) }
    const toggleSwitch = $('<a href="#">Toggle</a>').click((change) => {
        cardBody.toggle(components.openCards[block.title] = !components.openCards[block.title])
        setToggleMsg($(change.target))
        return false
    })
    setToggleMsg(toggleSwitch)
    card.append($('<div />').addClass('block-card-toggle').append(toggleSwitch))
    card.append(cardBody)
    return $('<div class="block-card-outer col-xl-3 col-lg-4 col-md-6 col-12"></div>').append(card)
}

components.stateBox = (item, onClick) => {
    const stateBoxDetails = components._stateIcons(item)
    stateBoxDetails.value.click(function(change) {
        var state = change.target.dataset.state
        onClick(item.id, state)
        return false
    })
    let msg = stateBoxDetails.value
    if (item.position) msg.append(' ', prettyDuration(item.position))
    return $('<div></div>')
        .append(msg)
        .addClass(stateBoxDetails.className)
}

components._stateIcons = (item) => {
    let desc = ' ' + item.state
    if (item.state == 'PAUSED' && item.hasOwnProperty('buffering_percent') && item.buffering_percent !== 100) {
        desc = ' BUFFERING (' + item.buffering_percent + '%)'
    }
    else if (item.desired_state && item.desired_state !== item.state) {
        desc = ' ' + item.state + ' &rarr; ' + item.desired_state
    }
    const allIcons = $('<div class="state-icons"></div>').append([
        components.stateIcon('NULL', item.state),
        components.stateIcon('READY', item.state),
        components.stateIcon('PAUSED', item.state),
        components.stateIcon('PLAYING', item.state), desc])
    return {value: allIcons, className: item.state}
}

components.volumeInput = (volume) => {
    const DEFAULT_VOLUME = 1.0
    if (volume === undefined || volume === null) volume = DEFAULT_VOLUME
    volume *= 100 // as it's a percentage
    return formGroup({
        id: 'input-volume',
        label: 'Volume',
        name: 'volume',
        type: 'text',
        'data-slider-min': 0,
        'data-slider-max': 100,
        'data-slider-step': 10,
        'data-slider-value': volume
    })
}

components.hideDetails = () => '<i class="fas fa-caret-down"></i> Hide details'
components.showDetails = () => '<i class="fas fa-caret-right"></i> Show details'

components.getMixOptions = (src) => {
    return mixersHandler.items.map(mixer => {
        if (!mixer.sources) return
        if (src === mixer) return
        var foundThis = mixer.sources.find(x => x.uid === src.uid)
        var inMix = foundThis && foundThis.in_mix ? 'In mix' : 'Not in mix'
        var div = $('<div class="mix-option"></div>')
        if (foundThis && foundThis.in_mix) {
            div.addClass('mix-option-showing')
            var removeButton = components.removeButton()
            removeButton.click(() => { mixersHandler.remove(mixer, src); return false })
            var buttons = $('<div class="option-icons"></div>')
            buttons.append([removeButton])
            div.append(buttons)
        }
        else {
            div.addClass('mix-option-hidden')
            var cutButton = components.cutButton()
            cutButton.click(() => { mixersHandler.cut(mixer, src); return false })
            var overlayButton = components.overlayButton()
            overlayButton.click(() => { mixersHandler.overlay(mixer, src); return false })
            var buttons = $('<div class="option-icons"></div>')
            buttons.append([cutButton, overlayButton])
            div.append(buttons)
        }
        div.append('<strong>Mixer ' + mixer.id + ':</strong> ' + inMix)
        return div
    }).filter(x => !!x)
}
