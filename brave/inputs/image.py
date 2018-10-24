from brave.inputs.input import Input
from gi.repository import Gst
import brave.config as config


class ImageInput(Input):
    '''
    Handles an image input.
    Freezes the image to create a video stream.
    '''

    def has_audio(self):
        return False

    def permitted_props(self):
        return {
            'uri': {
                'type': 'str',
            },
            'width': {
                'type': 'int'
            },
            'height': {
                'type': 'int'
            },
            'xpos': {
                'type': 'int',
                'default': 0
            },
            'ypos': {
                'type': 'int',
                'default': 0
            },
            'zorder': {
                'type': 'int',
                'default': 1
            }
        }

    def create_elements(self):
        if not config.enable_video():
            return

        # To crop (not resize): videobox autocrop=true border-alpha=0
        pipeline_string = ('uridecodebin name=uridecodebin uri="' + self.props['uri'] +
                           '" ! imagefreeze ! videoconvert ! video/x-raw,pixel-aspect-ratio=1/1,framerate=30/1 ! '
                           'intervideosink sync=true name=intervideosink')
        if not self.create_pipeline_from_string(pipeline_string):
            return False
        self.intervideosink = self.pipeline.get_by_name('intervideosink')
        self.uridecodebin = self.pipeline.get_by_name('uridecodebin')
        if self.intervideosink is None:
            raise Exception('Unable to make image input - cannot find intervideosink')

        self.create_intervideosrc_and_connections()
        self.handle_updated_props()
        self.pipeline.set_state(Gst.State.PLAYING)

    def get_input_cap_props(self):
        '''
        Gets the width/height of the input.
        '''

        element = self.uridecodebin
        if not element:
            return
        pad = element.get_static_pad('src_0')
        if not pad:
            return
        caps = pad.get_current_caps()
        if not caps:
            return
        size = caps.get_size()
        if size == 0:
            return

        structure = caps.get_structure(0)
        props = {'video_caps_string': structure.to_string()}
        if structure.has_field('height'):
            props['height'] = structure.get_int('height').value
        if structure.has_field('width'):
            props['width'] = structure.get_int('width').value

        return props
