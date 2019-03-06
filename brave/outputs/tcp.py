from brave.outputs.output import Output
import socket
import brave.config as config


class TCPOutput(Output):
    '''
    For outputing as a TCP server (which VLC can play)
    '''

    def permitted_props(self):
        return {
            **super().permitted_props(),
            'host': {
                'type': 'str',
                'required': True
            },
            'port': {
                'type': 'int',
                'required': True
            },
            'width': {
                'type': 'int',
                'default': config.default_mixer_width()
            },
            'height': {
                'type': 'int',
                'default': config.default_mixer_height()
            },
            'audio_bitrate': {
                'type': 'int',
                'default': 128000
            },
            'container': {
                'type': 'str',
                'default': 'mpeg',
                'permitted_values': {
                    'mpeg': 'MPEG',
                    'ogg': 'OGG'
                }
            }
        }

    def create_elements(self):
        '''
        Create the elements needed whether this is audio, video, or both
        '''
        mux_type = 'oggmux' if self.container == 'ogg' else 'mpegtsmux'
        video_encoder_type = 'theoraenc' if self.container == 'ogg' else 'x264enc'
        audio_encoder_type = 'vorbisenc' if self.container == 'ogg' else 'avenc_ac3'

        pipeline_string = 'queue name=queue ! tcpserversink name=sink'

        # We only want a mux if there's video:
        has_mux = config.enable_video
        if has_mux:
            pipeline_string = f'{mux_type} name=mux ! {pipeline_string}'

        if config.enable_video():
            pipeline_string += ' ' + self._video_pipeline_start() + video_encoder_type + ' name=encoder ! queue ! mux.'

        if config.enable_audio():
            audio_bitrate = self.audio_bitrate

            # Having default_audio_caps() in the pipeline stops them from changing and interrupting the encoder.
            audio_pipeline_string = ('interaudiosrc name=interaudiosrc ! ' + config.default_audio_caps() +
                                     ' ! audioconvert ! audioresample ! %s name=audio_encoder bitrate=%d') % \
                (audio_encoder_type, audio_bitrate)
            if has_mux:
                audio_pipeline_string += f' ! queue ! mux.'
            else:
                audio_pipeline_string += ' ! queue.'

            pipeline_string = pipeline_string + ' ' + audio_pipeline_string

        self.create_pipeline_from_string(pipeline_string)

        if config.enable_video():
            # pass
            if self.container == 'mpeg':
                # Testing has shown 60 (i.e. once every 2s at 30 fps) works best
                self.pipeline.get_by_name('encoder').set_property('key-int-max', 60)

            # tune=zerolatency reduces the delay of TCP output
            # self.pipeline.get_by_name('encoder').set_property('tune', 'zerolatency')

        if not hasattr(self, 'host'):
            self.host = socket.gethostbyname(socket.gethostname())
        if not hasattr(self, 'port'):
            self.port = self._get_next_available_port()

        sink = self.pipeline.get_by_name('sink')
        sink.set_property('port', int(self.port))
        sink.set_property('host', self.host)
        sink.set_property('recover-policy', 'keyframe')
        sink.set_property('sync', False)

        self.logger.info('TCP output created at tcp://%s:%s' % (self.host, self.port))

    def _get_next_available_port(self):
        ports_in_use = self.get_ports_in_use()
        PORT_RANGE_START = 7000
        port = PORT_RANGE_START
        while True:
            if port not in ports_in_use:
                return port
            port += 1

    def get_ports_in_use(self):
        ports_in_use = []
        for name, output in self.session().outputs.items():
            if hasattr(self, 'port'):
                ports_in_use.append(int(output.port))
        return ports_in_use

    def create_caps_string(self):
        # x264enc cannot accept RGB format, so we move to one that it does (I420)
        return super().create_caps_string(format='I420')
