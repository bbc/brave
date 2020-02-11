from brave.outputs.output import Output
import brave.config as config


class RTMPOutput(Output):
    '''
    For sending an output to a third-party RTMP server (such as Facebook Live).
    '''

    def permitted_props(self):
        return {
            **super().permitted_props(),
            'uri': {
                'type': 'str'
            },
            'width': {
                'type': 'int',
                'default': config.default_mixer_width()
            },
            'height': {
                'type': 'int',
                'default': config.default_mixer_height()
            }
        }

    def create_elements(self):
        '''
        Create the elements needed whether this is audio, video, or both
        '''
        pipeline_string = 'flvmux name=mux streamable=true ! rtmpsink name=sink '

        if config.enable_video():
            # key-int-max=60 puts a keyframe every 2 seconds (60 as 2*framerate)
            pipeline_string += ' ' + self._video_pipeline_start() + \
                'x264enc name=video_encoder tune=zerolatency key-int-max=30 ! h264parse ! queue ! mux.'

        if config.enable_audio():
            pipeline_string += ' ' + self._audio_pipeline_start() + \
                'avenc_aac name=audio_encoder ! aacparse ! audio/mpeg, mpegversion=4 ! queue ! mux.'

        self.create_pipeline_from_string(pipeline_string)
        self.pipeline.get_by_name('sink').set_property('location', self.uri + ' live=1')

        self.logger.info('RTMP output now configured to send to ' + self.uri)

    def create_caps_string(self):
        # framerate=30/1 because Facebook Live and YouTube live want this framerate.
        # profile=baseline may be superflous but some have recommended it for Facebook
	# need to look a this some more, to see what else can be tuned up
        #return super().create_caps_string(format='I420') + ',framerate=30/1,profile=baseline'
        return super().create_caps_string(format='I420') + ',framerate=30/1,profile=baseline'
