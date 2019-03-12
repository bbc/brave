Vue.component('preview-button', {
    template: `<b-dropdown variant="info" size="sm">
        <template slot="button-content">
            <i class="fas fa-tv"></i>&nbsp;&nbsp; {{msg}}
        </template>
        <template v-if="blocksThatCanBePreviewed.length == 0">
            <b-dropdown-item disabled>There are no inputs or mixers to preview.</b-dropdown-item>
        </template>
        <template v-else>
            <b-dropdown-item v-on:click="selectBlock(null, null)" key="no-preview">No preview</b-dropdown-item>
            <b-dropdown-divider />
            <b-dropdown-item v-for="block in blocksThatCanBePreviewed"  v-on:click="selectBlock(block.uid, 'webrtc')" v-bind:key="block.uid + '-webrtc'">{{$root.prettyUid(block.uid)}} (as WebRTC stream)</b-dropdown-item>
            <b-dropdown-divider />
            <b-dropdown-item v-for="block in blocksThatCanBePreviewed"  v-on:click="selectBlock(block.uid, 'image')" v-bind:key="block.uid + '-image'">{{$root.prettyUid(block.uid)}} (as updating image)</b-dropdown-item>
        </template>
    </b-dropdown>`,
    computed: {
        blocksThatCanBePreviewed: function() {
            return this.$root.blocks.filter(b => ['input', 'mixer'].indexOf(b.block_type) !== -1)
        },
        msg: function() {
            if (this.$root.previewBlockUid && this.$root.previewBlockFormat) {
                return `${this.$root.prettyUid(this.$root.previewBlockUid)} (${this.$root.prettyType(this.$root.previewBlockFormat)})`
            }
            return 'No preview'
        }
    },
    methods: {
        selectBlock: function(uid, format) {
            this.$root.previewBlockUid = uid
            this.$root.previewBlockFormat = format
            if (uid && format) {
                let output = this.$root.outputForSource(uid, format, true)
                console.log('output uid=', output)
            }
        }
    }
})

Vue.component('preview-bar', {
    template: `<div v-if="canShow" id="preview-bar">
        <preview-image v-if="$root.previewBlockFormat === 'image'" :block="previewBlock" />
        <preview-webrtc v-if="$root.previewBlockFormat === 'webrtc'" :block="previewBlock" />
    </div>`,
    computed: {
        previewBlock: function() {
            return this.$root.previewBlockUid ? this.$root.blockByUid(this.$root.previewBlockUid) : null
        },
        canShow: function() {
            return this.$root.previewBlockFormat && this.previewBlock
        }
    }
})

Vue.component('preview-image', {
    props: ['block'],
    template: '<img :src="url" />',
    data: function() {
        return {
            randomNumber: 0
        }
    },
    computed: {
        url: function() {
            return '/api/outputs/' + this.outputId + '/body?' + this.randomNumber
        },
        outputId: function() {
            return this.$root.outputForSource(this.block.uid, 'image', false)
        }
    },
    created: function () {
        setInterval(() => { this.randomNumber = Math.floor(Date.now()/100) }, 500)
    }  
})

Vue.component('preview-webrtc', {
    props: ['block'],
    template: `<video id="stream" autoplay="true" :srcObject.prop="$root.webrtcSrc"/>`,
    destroyed: function() {
        webrtc.close()
    },
    created: function () {
        webrtc.requestConnection(this.outputId)
        console.log('webrtc created with output', this.outputId)
    },
    computed: {
        outputId: function() {
            return this.$root.outputForSource(this.block.uid, 'webrtc', false)
        }
    },
})


