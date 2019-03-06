Vue.component('block-row', {
    props: ['block'],
    template: `<tr v-on:click="$root.selectBlock(block.uid)" :class="{ 'block-selected': selected }"">
        <th>{{ this.prettyUid(block.uid) }}</th>
        <block-summary :block="block" />
        <state-box :block="block" />
    </tr>`,
    computed: {
        selected: function() {
            return this.$root.selectedBlockUid === this.block.uid
        }
    },
    methods: {
        stateBox: function() {
            return ``
        }
    }
})

Vue.component('block-summary', {
    props: ['block'],
    template: '<td>{{msg}}</td>',
    computed: {
        msg: function() {
            if (this.block.uri) return this.block.uri
            const prettyType = this.ucFirst(this.prettyType(this.block.type))
            if (this.block.text) return prettyType + ' (' + this.block.text + ')'
            return prettyType
        }
    }
})

Vue.component('state-box', {
    props: ['block'],
    template: `<td v-if="block.state" :class="block.state">
        <state-icons :block="block" /> <span v-html="msg"></span>
    </td>
    <td v-else></td>`,
    computed: {
        msg: function() {
            let m = this.block.state 
            if (this.block.desired_state && this.block.desired_state !== this.block.state) {
                m += ' &rarr; ' + this.block.desired_state
            }
            return m
        }
    }
})

Vue.component('state-icons', {
    props: ['block'],
    template: `
    <span class="state-icons">
        <icon name="NULL" :extraClass="block.state==='NULL' ? '' : 'icon-unselected'"  v-on:click="$root.postUpdate(block, {state:'NULL'})" />
        <icon name="READY" :extraClass="block.state==='READY' ? '' : 'icon-unselected'" v-on:click="$root.postUpdate(block, {state:'READY'})" />
        <icon name="PAUSED" :extraClass="block.state==='PAUSED' ? '' : 'icon-unselected'" v-on:click="$root.postUpdate(block, {state:'PAUSED'})" />
        <icon name="PLAYING" :extraClass="block.state==='PLAYING' ? '' : 'icon-unselected'" v-on:click="$root.postUpdate(block, {state:'PLAYING'})" />
    </span>`,
    computed: {
        selectedState: function() { return block.state }
    }
})

Vue.component('icon', {
    props: ['name', 'extraClass', 'onClick'],
    computed: {
        nameToClass: function() {
            const icons = {
                'PLAYING': 'fa-play',
                'PAUSED': 'fa-pause',
                'READY': 'fa-stop',
                'NULL': 'fa-exclamation-triangle',
                'close': 'fa-times',
            }
            return icons[this.name]
        }
    },
    template: `<a href="#" :class="['fas', nameToClass, extraClass]" v-on:click.stop="$emit('click')" ></a>`
})

Vue.component('rhs', {
    template: `<div class="rhs-box" v-if="this.block">
        <icon name="close" extraClass="close-button" v-on:click="$root.selectBlock(null)" />
        <h2>{{title}}</h2>
        <block-details-table :block="this.block" />
        <div style="margin-top: 20px">
            <delete-block-button :block="this.block" />
        </div>
    </div>`,
    computed: {
        block: function() { return this.$root.blocks.find(b => b.uid === this.$root.selectedBlockUid) },
        title: function() {
            let title = this.prettyUid(this.block.uid)
            if (this.block.type && this.block.type !== this.uidToTypeAndId(this.block.uid).type) title += ' (' + this.prettyType(this.block.type) + ')'
            return title
        }
    }
})

Vue.component('block-details-table', {
    props: ['block'],
    template: `
    <table class="details-table">
    <tr v-if="this.block.hasOwnProperty('volume')"><th>Volume</th><td><block-volume :volume="this.block.volume" /></td></tr>
    <tr v-if="this.block.hasOwnProperty('width')"><th>Dimensions</th><td><block-size :block="this.block" /></td></tr>
    <tr v-if="this.block.hasOwnProperty('pattern')"><th>Pattern</th><td><block-pattern :value="this.block.pattern" /></td></tr>
    <tr v-if="this.block.hasOwnProperty('wave')"><th>Wave</th><td><block-wave :value="this.block.wave" /></td></tr>
    <tr v-if="this.block.hasOwnProperty('freq')"><th>Frequency</th><td>{{this.block.freq}}</td></tr>
    <tr v-if="this.block.hasOwnProperty('uri')"><th>URI</th><td>{{this.block.uri}}</td></tr>
    <tr v-if="this.block.hasOwnProperty('text')"><th>Text</th><td>{{this.block.text}}</td></tr>
    <tr v-if="this.block.hasOwnProperty('host')"><th>Host</th><td>{{this.block.host}}</td></tr>
    <tr v-if="this.block.hasOwnProperty('port')"><th>Port</th><td>{{this.block.port}}</td></tr>
    <tr v-if="this.block.hasOwnProperty('location')"><th>Location</th><td>{{this.block.location}}</td></tr>
    <tr v-if="this.block.hasOwnProperty('stream_name')"><th>Stream name</th><td>{{this.block.stream_name}}</td></tr>
    </table>
    `
})

Vue.mixin({
    methods: {
        ucFirst: str => str.charAt(0).toUpperCase() + str.slice(1),
        uidToTypeAndId: uid => {
            const matches = uid.match(/^(input|mixer|output|overlay)(\d+)$/)
            return matches ? {type: matches[1], id: matches[2]} : null
        },
        prettyUid: function(uid) {
            if (!uid) return uid
            const details = this.uidToTypeAndId(uid)
            return details ? this.ucFirst(details.type + ' ' + details.id) : uid
        },
        allBlocks: function() {
            return this.blocks.mixers
        },
        prettyType: function(t) {
            if (t === 'tcp_client') return 'TCP Client'
            if (t === 'uri') return 'URI'
            return t.replace(/_/g, ' ')
        },
    }
  })
  
const app = new Vue({
    el: '#app',
    data: {
      selectedBlockUid: null,      
      foo: 'bar',
      blocks: [],
      cpu: '',
      alertMsg: null,
    },
    computed: {
        sortedBlocks: function() {
            function compare(a, b) {
                if (a.block_type_plural === b.block_type_plural) return a.id - b.id
                if (a.block_type_plural === 'inputs') return -1
                if (b.block_type_plural === 'inputs') return 1
                if (a.block_type_plural === 'overlays') return -1
                if (b.block_type_plural === 'overlays') return 1
                if (a.block_type_plural === 'mixers') return -1
                if (b.block_type_plural === 'mixers') return 1
                return a.id - b.id
            }
            return this.blocks.sort(compare)
        }
    },
    methods: {
        selectBlock: function(uid) {
            if (uid && uid !== this.selectedBlockUid) {
                this.selectedBlockUid = uid
            }
            else {
                this.selectedBlockUid = null
            }
        },
        postUpdate: function(block, update) {
            const uri = `/api/${this.uidToTypeAndId(block.uid).type}s/${block.id}`
            axios.post(uri, update).then(response => {
                if (response.status !== 200) {
                    console.error('Failed to update')
                }
            })
        },
        putToApi: function(blockType, details) {
            const uri = `/api/${blockType}s`
            return axios.put(uri, details)
            .then(response => {
                if (response.data && response.data.uid) this.selectBlock(response.data.uid)                    
            })
            .catch(err => {
                if (err.response && err.response.data && err.response.data.error) {
                    this.alertMsg = err.response.data.error
                }
                else {
                    this.alertMsg = 'Failed to create ' + blockType
                }
            })
        },
        deleteToApi: function(block) {
            const uri = `/api/${block.block_type_plural}/${block.id}`
            return axios.delete(uri).then(response => {
                if (response.status !== 200) {
                    console.error('Failed to delete', blockType, id)
                }
            })
        },
        fetchData: function() {
            const url = 'api/all'
            axios.get(url).then(response => {
                let blocks = []
                for (let block_type in response.data) {
                    response.data[block_type].forEach(b => { b.block_type_plural = block_type })
                    blocks = blocks.concat(response.data[block_type])
                }

                // Only do if the object has changed to stop needless DOM updates
                if (JSON.stringify(this.blocks) !== JSON.stringify(blocks)) {
                    this.blocks = blocks
                }
            })
            setTimeout(this.fetchData, POLL_FREQUENCY)
        }
    },
    mounted() {
        this.fetchData()
    }
})



function start() {
    websocket.setup()
}

