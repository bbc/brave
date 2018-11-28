from brave.outputs.output import Output
import brave.config as config
import brave.exceptions
import os


class KvsOutput(Output):
    '''
    For outputting to AWS's Kinesis Video Stream
    '''

    def permitted_props(self):
        return {
            **super().permitted_props(),
            'width': {
                'type': 'int',
                'default': 640,
            },
            'height': {
                'type': 'int',
                'default': 360
            },
            'stream_name': {
                'type': 'str'
            }
        }

    def create_elements(self):
        if not config.enable_video():
            return

        access_key = os.environ['AWS_ACCESS_KEY_ID']
        secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
        if not access_key:
            raise brave.exceptions.InvalidConfiguration('Missing AWS_ACCESS_KEY_ID environemnt variable')
        if not secret_key:
            raise brave.exceptions.InvalidConfiguration('Missing AWS_SECRET_ACCESS_KEY environemnt variable')

        self._create_initial_multiqueue()

        video_caps = 'video/x-raw,format=I420,width=%d,height=%d,pixel-aspect-ratio=1/1,framerate=30/1' % \
            (self.props['width'], self.props['height'])

        pipeline_string = ('intervideosrc name=intervideosrc ! videoconvert ! videoscale ! ' +
                           video_caps +
                           # 'video/x-raw,format=I420,width=640,height=480,framerate=30/1 ! '
                           ' ! x264enc bframes=0 key-int-max=45 bitrate=500 ! '
                           'video/x-h264,stream-format=avc,alignment=au ! '
                           'kvssink name=kvssink')

        if not self.create_pipeline_from_string(pipeline_string):
            self.logger.error('TEMP cannot create pipeline from string:%s' % pipeline_string)
            return False

        kvssink = self.pipeline.get_by_name('kvssink')
        kvssink.set_property('access-key', access_key)
        kvssink.set_property('secret-key', secret_key)
        kvssink.set_property('stream-name', self.props['stream_name'])

        self.intervideosrc = self.pipeline.get_by_name('intervideosrc')
        self.intervideosrc_src_pad = self.intervideosrc.get_static_pad('src')
        self.create_intervideosink_and_connections()
