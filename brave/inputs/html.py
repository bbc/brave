from brave.inputs.input import Input
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
            **super().permitted_props(),
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

        self.create_pipeline_from_string('cef url="' + self.uri + '" ! '
                                         ' videoconvert ! video/x-raw,format=ARGB ! '
                                         'queue' + self.default_video_pipeline_string_end())

        self.intervideosink = self.pipeline.get_by_name('intervideosink')
        self.final_video_tee = self.pipeline.get_by_name('final_video_tee')
        self.video_output_queue = self.pipeline.get_by_name('video_output_queue')

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
