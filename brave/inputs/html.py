from brave.inputs.input import Input
from gi.repository import Gst
import brave.config as config


class HTMLInput(Input):
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
                'defatult': 'https://www.bbc.co.uk'
            },
            'width': {
                'type': 'int',
                'default': 1280
            },
            'height': {
                'type': 'int',
                'default': 720
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

        if not self.create_pipeline_from_string('cef url="' + self.props['uri'] + '" ! '
                                                ' videoconvert ! video/x-raw,format=ARGB ! '
                                                'queue ! intervideosink sync=true name=intervideosink'):
            return False

        self.intervideosink = self.pipeline.get_by_name('intervideosink')
        if self.intervideosink is None:
            raise Exception('Unable to make image input - cannot find intervideosink')

        self.create_intervideosrc_and_connections()
        self.handle_updated_props()
        self.pipeline.set_state(Gst.State.PLAYING)

    def get_input_cap_props(self):
        '''
        Gets the width/height of the input.
        '''

        element = self.intervideosink
        if not element:
            return
        caps = element.get_static_pad('sink').get_current_caps()
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
