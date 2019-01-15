from brave.outputs.output import Output
import brave.config as config
import os
import random


class ImageOutput(Output):
    '''
    For creating an image file of the output.
    '''

    def permitted_props(self):
        return {
            **super().permitted_props(),
            'width': {
                'type': 'int',
                'default': 640
            },
            'height': {
                'type': 'int',
                'default': 360
            },
            'update_frequency': {
                'type': 'int',
                'default': 1
            },
            'location': {
                'type': 'str',
                # TODO reconsider this default:
                'default': '/usr/local/share/brave/output_images/img_%d.jpg' % random.randint(10000, 20000)
            }
        }

    def has_audio(self):
        return False

    def create_caps_string(self):
        return super().create_caps_string(format='RGB') + ',framerate=1/' + str(self.update_frequency)

    def create_elements(self):
        if not config.enable_video():
            return
        self.__delete_file_if_exists()
        pipeline_string = self._video_pipeline_start() + 'jpegenc ! multifilesink name=sink'
        self.create_pipeline_from_string(pipeline_string)
        sink = self.pipeline.get_by_name('sink')
        sink.set_property('location', self.location)

    def __delete_file_if_exists(self):
        try:
            os.remove(self.location)
        except FileNotFoundError:
            pass
