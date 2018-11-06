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
                'type': 'str'
            },
            'port': {
                'type': 'str'
            },
            'width': {
                'type': 'int'
            },
            'height': {
                'type': 'int'
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

        self._create_initial_multiqueue()
        mux_type = 'oggmux' if self.props['container'] == 'ogg' else 'mpegtsmux'
        video_encoder_type = 'theoraenc' if self.props['container'] == 'ogg' else 'x264enc'
        audio_encoder_type = 'vorbisenc' if self.props['container'] == 'ogg' else 'avenc_ac3'

        pipeline_string = 'queue leaky=2 name=queue ! tcpserversink name=sink'

        # We only want a mux if there's video:
        has_mux = config.enable_video
        if has_mux:
            pipeline_string = f'{mux_type} name=mux ! {pipeline_string}'

        if config.enable_video():
            video_pipeline_string = (f'intervideosrc name=intervideosrc ! videoconvert ! '
                                     f'videoscale ! videorate ! '
                                     f'{self.create_caps_string()} ! '
                                     f'{video_encoder_type} name=encoder ! queue ! mux.')

            pipeline_string = pipeline_string + ' ' + video_pipeline_string

        if config.enable_audio():
            audio_bitrate = self.props['audio_bitrate']

            audio_pipeline_string = ('interaudiosrc name=interaudiosrc ! audioconvert ! '
                                     'audioresample ! %s name=audio_encoder bitrate=%d') % \
                (audio_encoder_type, audio_bitrate)
            if has_mux:
                audio_pipeline_string += f' ! queue max-size-bytes={10*(2 ** 20)} ! mux.'
            else:
                audio_pipeline_string += ' ! queue.'

            pipeline_string = pipeline_string + ' ' + audio_pipeline_string

        if not self.create_pipeline_from_string(pipeline_string):
            return False

        if config.enable_video():
            encoder = self.pipeline.get_by_name('encoder')
            self.intervideosrc = self.pipeline.get_by_name('intervideosrc')
            self.intervideosrc_src_pad = self.intervideosrc.get_static_pad('src')

            if self.props['container'] == 'mpeg':
                encoder.set_property('key-int-max', 120)  # 4x 30fps TODO not hard-code

            # tune=zerolatency reduces the delay of TCP output
            # encoder.set_property('tune', 'zerolatency')

            self.create_intervideosink_and_connections()

        if config.enable_audio():
            self.interaudiosrc = self.pipeline.get_by_name('interaudiosrc')
            self.interaudiosrc_src_pad = self.interaudiosrc.get_static_pad('src')
            # audio_encoder = self.pipeline.get_by_name('audio_encoder')
            # audio_encoder.set_property('bitrate', 48000)
            self.create_interaudiosink_and_connections()

        if 'host' not in self.props:
            self.props['host'] = socket.gethostbyname(socket.gethostname())
        if 'port' not in self.props:
            self.props['port'] = self._get_next_available_port()

        sink = self.pipeline.get_by_name('sink')
        sink.set_property('port', int(self.props['port']))
        sink.set_property('host', self.props['host'])
        sink.set_property('recover-policy', 'keyframe')
        sink.set_property('sync', False)

        self.logger.info('TCP output created at tcp://%s:%s' % (self.props['host'], self.props['port']))

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
            if 'port' in output.props:
                ports_in_use.append(int(output.props['port']))
        return ports_in_use
