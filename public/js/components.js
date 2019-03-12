Vue.component('alert', {
    template: `<b-alert variant="danger" dismissible v-model="showAlertMsg">
        {{$root.alertMsg}}
    </b-alert>`,
    computed: {
        showAlertMsg: {
            get: function() {
                return !!this.$root.alertMsg
            },
            set: function() {
                return this.$root.alertMsg = null
            }
        }
    }
})

Vue.component('restart-modal', {
    template: `<div><b-modal ref="restartModal" id="restart-modal" title="Restart Brave" hide-footer>
        <p>When restarting Brave, should the current configuration (inputs, etc.) be retained?</p>
        <b-button variant="primary" block @click="restartWithCurrentConfig">Yes, restart Brave and keep the current configuration</b-button>
        <b-button variant="primary" block @click="restartWithOriginalConfig">No, restart Brave with the original configuration</b-button>    
    </b-modal></div>`,
    methods: {
        restartWithCurrentConfig: function() {
            return this.handleRestart('current')
        },
        restartWithOriginalConfig: function() {
            return this.handleRestart('original')
        },
        handleRestart: function(config) {
            const uri = `/api/restart`
            axios.post(uri, {config}).then(response => {
                if (response.status !== 200) {
                    app.alertMsg = 'Request to restart Brave failed'
                }
            })
            this.$refs.restartModal.hide()
        }
    }
})

Vue.component('create-overlay-modal', {
    template: `<b-modal size="lg"  ref="createOverlayModal" id="create-overlay-modal" title="Create new overlay" hide-footer>
        <p>What type of overlay?</p>
        <b-button variant="primary" block v-on:click="createOverlay('text')">Text</b-button>
        <b-button variant="primary" block v-on:click="createOverlay('clock')">Clock</b-button>    
        <b-button variant="primary" block v-on:click="createOverlay('effect')">Effect</b-button>    
    </b-modal>`,
    methods: {
        createOverlay: function(type) {
            this.$root.putToApi('overlay', {type})
            this.$refs.createOverlayModal.hide()
        }
    }
})

Vue.component('create-input-modal', {
    template: `<b-modal size="lg" ref="createinputModel" id="create-input-modal" title="Create new input" hide-footer @shown="modalShown">
    <div v-if="this.type === 'uri' || this.type === 'image'">
        <p>What's the URI?</p>
        <b-form-input v-model="uri" type="text" placeholder="Enter URI" />
        <b-button variant="primary" block v-on:click="submitUri()">Create</b-button>
        <div>RTMP example: <code>rtmp://184.72.239.149/vod/BigBuckBunny_115k.mov</code></div>
        <div>RTSP example: <code>rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov</code></div>
        <div>Local file example: <code>file:///tmp/my_movie.mp4</code></div>
    </div>
    <div v-else-if="this.type === 'tcp_client'">
        <p>What is the TCP server host name?</p>
        <b-form-input v-model="host" type="text" placeholder="Enter host" />
        <div>(e.g. <code>localhost</code>)</div>
        <p>What is the TCP server port?</p>
        <b-form-input v-model="port" type="number" placeholder="Enter port" />
        <b-button variant="primary" block v-on:click="submitHost()">Create</b-button>
        <div>(e.g. <code>8000</code>)</div>
    </div>
    <div v-else>
            <p>What type of input?</p>
            <b-button variant="primary" block v-on:click="createOverlay('uri')">URI (for files, RTMP, RTSP and HLS)</b-button>
            <b-button variant="primary" block v-on:click="createOverlay('image')">Image</b-button>
            <b-button variant="primary" block v-on:click="createOverlay('tcp_client')">TCP Client (receive from a TCP server)</b-button>
            <b-button variant="primary" block v-on:click="createOverlay('html')">HTML (for showing a web page)</b-button>
            <b-button variant="primary" block v-on:click="createOverlay('decklink')">Decklink Device</b-button>
            <b-button variant="primary" block v-on:click="createOverlay('test_video')">Test video stream</b-button>
            <b-button variant="primary" block v-on:click="createOverlay('test_audio')">Test audio stream</b-button>
        </div>
    </b-modal>`,
    data: function () {
        return {
            type: null,
            uri: null,
            host: null,
            port: null
        }
    },
    methods: {
        modalShown: function() {
            this.type = null
        },
        submitUri: function() {
            this.$root.putToApi('input', {type: this.type, uri: this.uri})
            this.$refs.createinputModel.hide()
        },
        submitHost: function() {
            this.$root.putToApi('input', {type: this.type, host: this.host, port: this.port})
            this.$refs.createinputModel.hide()
        },
        createOverlay: function(type) {
            this.type = type
            if (type === 'uri' || type === 'image' || type === 'tcp_client') {
                // Nowt
            }
            else {
                this.$root.putToApi('input', {type})
                this.$refs.createinputModel.hide()
            }
        }
    }
})

Vue.component('create-output-modal', {
    template: `<b-modal size="lg" ref="createOutputModel" id="create-output-modal" title="Create new output" hide-footer @shown="modalShown">
    <div v-if="this.type === 'rtmp'">
        <p>What's the URI of the RTMP server to send to?</p>
        <b-form-input v-model="uri" type="text" placeholder="Enter URI" />
        <b-button variant="primary" block v-on:click="submitUri()">Create RTMP output</b-button>
        <div>e.g.: <code>rtmp://myserver.com/live/stream</code></div>
    </div>
    <div v-else-if="this.type === 'tcp'">
        <p>What is the hostname of the TCP server to send to?</p>
        <b-form-input v-model="host" type="text" placeholder="Enter host" />
        <div>(e.g. <code>localhost</code>)</div>
        <p>And what port should be used?</p>
        <b-form-input v-model="port" type="number" placeholder="Enter port" />
        <b-button variant="success" block v-on:click="submitHost()">Create TCP output</b-button>
        <div>(e.g. <code>8000</code>)</div>
    </div>
    <div v-else-if="this.type === 'file'">
        <p>What's the path (directory and filename) of the local file?</p>
        <b-form-input v-model="location" type="text" placeholder="Enter path" />
        <div>(e.g. <code>e.g. /tmp/foo.mp4</code>)</div>
        <b-button variant="primary" block v-on:click="submitFileLocation()">Create KVS stream output</b-button>
    </div>
    <div v-else-if="this.type === 'kvs'">
        <p>What is the KVS stream name?</p>
        <b-form-input v-model="stream_name" type="text" placeholder="Enter stream name" />
        <div>(e.g. <code>localhost</code>)</div>
        <b-button variant="primary" block v-on:click="submitKvsStreamName()">Create KVS stream output</b-button>
    </div>
    
    <div v-else>
        <p>What type of output?</p>
        <b-button variant="primary" block v-on:click="createOverlay('tcp')">TCP (server)</b-button>
        <b-button variant="primary" block v-on:click="createOverlay('rtmp')">RTMP (send to remote server)</b-button>
        <b-button variant="primary" block v-on:click="createOverlay('image')">JPEG image file every 1 second</b-button>
        <b-button variant="primary" block v-on:click="createOverlay('file')">File (Write audio/video to a local file)</b-button>
        <b-button variant="primary" block v-on:click="createOverlay('webrtc')">WebRTC for web preview</b-button>
        <b-button variant="primary" block v-on:click="createOverlay('kvs')">AWS Kinesis Video</b-button>
        <b-button variant="primary" block v-on:click="createOverlay('local')">Local (pop-up audio/video on this server, for debugging)</b-button>
    </div></b-modal>`,
    data: function () {
        return {
            type: null,
            host: null,
            port: null,
            location: null,
            stream_name: null
        }
    },
    methods: {
        modalShown: function() {
            this.type = null
        },
        submitUri: function() {
            this.$root.putToApi('output', {type: this.type, uri: this.uri})
            this.$refs.createOutputModel.hide()
        },
        submitHost: function() {
            this.$root.putToApi('output', {type: this.type, host: this.host, port: this.port})
            this.$refs.createOutputModel.hide()
        },
        submitKvsStreamName: function() {
            this.$root.putToApi('output', {type: this.type, stream_name: this.stream_name})
            this.$refs.createOutputModel.hide()
        },
        submitFileLocation: function() {
            this.$root.putToApi('output', {type: this.type, location: this.location})
            this.$refs.createOutputModel.hide()
        },
        createOverlay: function(type) {
            this.type = type
            if (type !== 'rtmp' && type !== 'tcp' && type !== 'kvs' && type !== 'file') {
                this.$root.putToApi('output', {type})
                this.$refs.createOutputModel.hide()
            }
        }
    }
})

Vue.component('delete-block-button', {
    props: ['block'],
    template: '<b-button variant="danger" block v-on:click="this.delete"><a href=\"#\" class=\"fas fa-trash-alt\" title=\"Delete\"></a> Delete</b-button>',
    methods: {
        delete: function() {
            if (confirm("Are you sure you want to delete " + this.block.uid + "?")) {
                this.$root.deleteToApi(this.block)
            }
        }
    }
})

Vue.component('top-bar-buttons', {
    template: `<span>
    <b-dropdown id="ddown1" variant="info" size="sm">
      <template slot="button-content">
        <i class="fas fa-plus"></i> Add
      </template>
      <b-dropdown-item v-b-modal.create-input-modal>Input</b-dropdown-item>
      <b-dropdown-item v-on:click="$root.putToApi('mixer', {})">Mixer</b-dropdown-item>
      <b-dropdown-item v-b-modal.create-output-modal>Output</b-dropdown-item>
      <b-dropdown-item v-b-modal.create-overlay-modal>Overlay</b-dropdown-item>
    </b-dropdown>
    <b-dropdown id="ddown1" variant="primary" size="sm">
      <template slot="button-content">
        <i class="fas fa-cog"></i> Options
      </template>
      <b-dropdown-item v-b-modal.restart-modal>Restart Brave</b-dropdown-item>
      <b-dropdown-item href="api/config/current.yaml">Download current config</b-dropdown-item>
      <b-dropdown-item v-on:click="$root.fetchData()">Refresh page</b-dropdown-item>
      <b-dropdown-item target="_blank" href="elements_table">Debug view (GStreamer elements)</b-dropdown-item>
    </b-dropdown>
  </span>`
})
