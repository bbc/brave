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
            raise brave.exceptions.InvalidConfiguration('Missing AWS_ACCESS_KEY_ID environment variable')
        if not secret_key:
            raise brave.exceptions.InvalidConfiguration('Missing AWS_SECRET_ACCESS_KEY environment variable')

        pipeline_string = (self._video_pipeline_start() + 'x264enc bframes=0 key-int-max=45 bitrate=500 ! '
                           'video/x-h264,stream-format=avc,alignment=au ! kvssink name=kvssink')

        self.create_pipeline_from_string(pipeline_string)

        kvssink = self.pipeline.get_by_name('kvssink')
        kvssink.set_property('access-key', access_key)
        kvssink.set_property('secret-key', secret_key)
        kvssink.set_property('stream-name', self.props['stream_name'])

    def create_caps_string(self):
        return super().create_caps_string() + ',format=I420,pixel-aspect-ratio=1/1,framerate=30/1'
