//
// This web interface has been quickly thrown together. It's not production code.
//

components = {}

components.closeButton = () => {
    return $("<a href=\"#\" class=\"fas fa-times close-button\" title=\"Close\"></a>")
}

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

components.checkCircle = () => {
    return $("<a href=\"#\" class=\"fas fa-check-circle\" title=\"Yes\"></a>")
}

components.stateIcon = (state, currentState, onClick) => {
    const selected = state == currentState
    const icons = {
        'PLAYING': 'fa-play',
        'PAUSED': 'fa-pause',
        'READY': 'fa-stop',
        'NULL': 'fa-exclamation-triangle'
    }
    const iconName = icons[state]
    const e = $('<a href=\"#\" class="fas ' + iconName + (selected ? '' : ' icon-unselected') + '" data-state="' + state + '" ></a>')
    e.click(onClick)
    return e
}

components.openCards = {}
components.selectedCard = null
components.card = (block) => {
    const card = $('<div class="block-card"></div>')
    if (components.selectedCard === block.uid) card.addClass('block-card-selected')
    card.click((change) => { onCardClick(block) })
    const header = $('<div class="block-card-head"></div>')
    if (block.title) header.append(block.title)
    if (block.options) {
        var options = $('<div class="option-icons"></div>')
        options.append(block.options)
        header.append(options)
    }
    card.append(header)
    if (block.state) card.append(P)
    // if (block.mixOptions) card.append(block.mixOptions)

    const cardBody = $('<div class="block-card-body"></div>')
    cardBody.append(block.body)
    if (!components.openCards[block.title]) cardBody.css('display', 'none')

    // const setToggleMsg = (target) => { target.html(components.openCards[block.title] ? components.hideDetails() : components.showDetails()) }
    // const toggleSwitch = $('<a href="#">Toggle</a>').click((change) => {
    //     cardBody.toggle(components.openCards[block.title] = !components.openCards[block.title])
    //     setToggleMsg($(change.target))
    //     return false
    // })
    // setToggleMsg(toggleSwitch)
    // card.append($('<div />').addClass('block-card-toggle').append(toggleSwitch))
    card.append(cardBody)
    return $('<div class="block-card-outer"></div>').append(card)
    //  col-xl-3 col-lg-4 col-md-6 col-12
}

function onCardClick(block) {
    const currentlySelected = components.selectedCard === block.uid
    if (components.selectedCard) {
        components.selectedCard = null
        components.rhs(null)
    }

    if (!currentlySelected) {
        components.selectedCard = block.uid
        components.rhs(block.uid)
    }

    drawAllItems()
}

components.rhs = (uid) => {
    components.current_rhs_uid = uid
    const rhs = $('#rhs')
    rhs.empty()
    if (!uid) return
    rhs.append(components._rhsBox(uid))
}

components.redrawRhs = () => {
    components.rhs(components.current_rhs_uid)
}

components.detailsTable = (fields) => {
    const table = $('<table class="details-table"></table>')
    fields.forEach(f => {
        const col1 = $('<th></th>').append(f[0])
        const col2 = $('<td></td>').append(f[1])
        const row = $(`<tr></tr>`).append(col1, col2) 
        table.append(row)
    })
    return table
}

components._rhsBox = (uid) => {
    const e = $('<div class="rhs-box"></div>')
    const uidDetails = uidToTypeAndId(uid)
    if (!uidDetails) return
    const handler = typeToHandler(uidDetails.type)
    if (!handler) return
    const block = handler.findById(uidDetails.id)
    let body = []
    body.push(components.closeButton().click(() => components.rhs(null)))
    let title = prettyUid(uid)
    if (block.type && block.type !== uidDetails.type) title += ' (' + block.type + ')'
    const boxHead = $('<h2/>').append(title)
    body.push(boxHead)

    if (handler.detailsForTable) {
        body = body.concat(components.detailsTable(handler.detailsForTable(block)))
    }

    if (handler.getMixOptions) {
        const mixOptions = handler.getMixOptions(block)
        if (mixOptions.length) {
            body = body.concat( $('<h3>Appears in...</h3>'), mixOptions)
        }
    }

    if (handler.getSourceOptions) {
        let sourceOptions = handler.getSourceOptions(block)
        if (!sourceOptions) sourceOptions = $('<div>There are no sources. Create some inputs or mixers!</div>')
        body = body.concat($('<h3>Sources</h3>'), sourceOptions)
    }

    const deleteButton = components.fullDeleteButton(uidDetails.type, title, () => handler.delete(block))
    body = body.concat( $('<h3>Actions</h3>'), deleteButton)

    e.append(body)
    return e
}

components.fullDeleteButton = (type, title, onClick) => {
    const b = $('<button type="button" class="btn btn-sm btn-danger">' +
                '<i class="fas fa-trash-alt"></i> Delete ' + type + '</button>')
    b.on('click', () => {
        if (window.confirm('Delete ' + title + '?')) onClick()
    })
    return b
}

components.fullCutInButton = (onClick) => {
    const b = $('<button type="button" class="btn btn-sm btn-success">' +
                '<i class="fas fa-cut"></i> Cut in</button>')
    b.on('click', onClick)
    return b
}

components.fullOverlayButton = (onClick) => {
    const b = $('<button type="button" class="btn btn-sm btn-success">' +
                '<i class="fas fa-layer-group"></i> Overlay</button>')
    b.on('click', onClick)
    return b
}

components.fullCutOutButton = (onClick) => {
    const b = $('<button type="button" class="btn btn-sm btn-warning">' +
                '<i class="fas fa-eye-slash"></i> Cut out</button>')
    b.on('click', onClick)
    return b
}

components.stateBox = (item, onClick) => {
    const stateBoxDetails = components._stateIcons(item, change => {
        onClick(item.id, change.target.dataset.state)
        return false
    })
    let msg = stateBoxDetails.value
    if (item.position) msg.append(' ', prettyDuration(item.position))
    return $('<div></div>')
        .append(msg)
        .addClass(stateBoxDetails.className)
}

components._stateIcons = (item, onClick) => {
    let desc = ' ' + item.state
    if (item.state == 'PAUSED' && item.hasOwnProperty('buffering_percent') && item.buffering_percent !== 100) {
        desc = ' BUFFERING (' + item.buffering_percent + '%)'
    }
    else if (item.desired_state && item.desired_state !== item.state) {
        desc = ' ' + item.state + ' &rarr; ' + item.desired_state
    }
    const allIcons = $('<div class="state-icons"></div>').append([
        components.stateIcon('NULL', item.state, onClick),
        components.stateIcon('READY', item.state, onClick),
        components.stateIcon('PAUSED', item.state, onClick),
        components.stateIcon('PLAYING', item.state, onClick), desc])
    return {value: allIcons, className: item.state}
}

components.slider = (currentValue, onChange, props) => {
    const wrapper = $(document.createElement('span'))
    const input = $(document.createElement('input'))
    wrapper.append(input)
    input.addClass('form-control form-control-sm')
    input.attr('type', 'text')
    input.attr('data-slider-min', props.min)
    input.attr('data-slider-max', props.max)
    input.attr('data-slider-step', props.step)
    input.attr('data-slider-value', currentValue)
    input.attr('id', props.id)

    input.slider();
    let msg = $('<span></span>')
    let showPerc = (val) => msg.text(val + props.text_end)
    showPerc(currentValue)
    const onSlide = (event) => {
        if (!event.value) return;
        if (event.value.oldValue === event.value.newValue) return
        showPerc(event.value.newValue)
        setTimeout(() => onChange(event.value.newValue), 1)
    }

    input.on('change', onSlide)
    wrapper.append(msg)
    return wrapper
}

// TODO remove this:
components.volumeInput = (volume) => {
    const DEFAULT_VOLUME = 0.8
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

components.switch = (val, onChange) => {
    const checkbox = $('<input type="checkbox"></input>')
    if (val) checkbox.prop('checked', true)
    checkbox.on('click', () => onChange(checkbox.is(":checked")))
    return $('<label class="switch" />').append(checkbox).append('<span class="switch-slider"></span>')
}

components.editableTextBox = (text, onChange) => {
    const wrapper = $('<span/>')
    const input = $('<input type="text" style="width:80%"/>')
    input.val(text)
    const yesButton = components.checkCircle().css({padding: '4px'})
    wrapper.append(input)
    wrapper.append(yesButton)
    yesButton.click(() => onChange(input.val()))
    // yesButton.on('click', onChange(input.val()))
    return wrapper
}

components.blocksTable = () => {
    const table = $('<table class="blocks-table"></table>')
    allBlocks().forEach(block => {
        const uidDetails = uidToTypeAndId(block.uid)
        if (!uidDetails) return
        const handler = typeToHandler(uidDetails.type)
        if (!handler) return
        const tr = $('<tr/>')
        let title = prettyUid(block.uid)
        if (block.type && block.type !== uidDetails.type) title += ' (' + block.type + ')'

        const th = $('<th />').append(title)
        tr.click(() => { onCardClick(block) })
        const td1 = $('<td />')
        if (uidDetails.type !== 'overlay') {
            td1.append(components.stateBox(block, handler.setState))
        }
        tr.append(th, td1)
        table.append(tr)
        if (components.selectedCard === block.uid) tr.addClass('block-selected')
    })
    return table
}