Vue.component('block-value', {
    props: ['value'],
    template: `<span>{{value}}</span>`
})

Vue.component('block-pattern', {
    props: ['value'],
    computed: {
        PATTERN_TYPES: function() { return PATTERN_TYPES }
    },
    template: `<select>
    <option v-for="(pattern, index) in PATTERN_TYPES" v-bind:value="index" :selected="value === index">
      {{ pattern }}
    </option>
  </select>
  `
})

Vue.component('block-wave', {
    props: ['value'],
    computed: {
        WAVE_TYPES: function() { return WAVE_TYPES }
    },
    template: `<select>
    <option v-for="(wave, index) in WAVE_TYPES" v-bind:value="index" :selected="value === index">
      {{ wave }}
    </option>
  </select>
  `
})

Vue.component('block-volume', {
    props: ['volume'],
    computed: {
    },
    template: `<span>{{volume}}%</span>
  `
})

function prettyDimensions(obj) {
    var str = obj.width + 'x' + obj.height
    if (obj.width*(9/16) === obj.height) {
        str += ' (16x9 landscape)'
    }
    else if (obj.width*(16/9) === obj.height) {
        str += ' (16x9 portrait)'
    }
    else if (obj.width*(3/4) === obj.height) {
        str += ' (4x3 landscape)'
    }
    else if (obj.width === obj.height) {
        str += ' (square)'
    }

    if (obj.width === 720 && obj.height === 576) str += ' (PAL DVD)'
    if (obj.width === 1280 && obj.height === 720) str += ' (720p HD)'
    if (obj.width === 1920 && obj.height === 1080) str += ' (1080p Full HD)'
    if (obj.width === 576 && obj.height === 520) str += ' (PAL SD)'
    if (obj.width === 1024 && obj.height === 576) str += ' (Widescreen SD)'
    if (obj.width === 1366 && obj.height === 768) str += ' (qHD)'
    return str
}

Vue.component('block-size', {
    props: ['block'],
    computed: {
        prettySize: function() { return prettyDimensions(this.block) }
    },
    template: `<span>{{prettySize}}</span>`
})
