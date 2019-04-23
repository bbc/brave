from brave.outputs.output import Output
import brave.config as config


class DecklinkOutput(Output):
    '''
    For previewing audio and video on a Decklink device.
    '''

    def permitted_props(self):
        return {
            **super().permitted_props(),
            'width': {
                'type': 'int',
                'default': 1280,
            },
            'height': {
                'type': 'int',
                'default': 720
            },
            'mode': {
                'type': 'int',
                'default': 17
            }
        }

    def create_elements(self):
        pipeline_string = ''
        if config.enable_video():
            pipeline_string += 'intervideosrc name=intervideosrc ! queue ! videoconvert ! videoscale ! decklinkvideosink device-number=0 mode=' + str(self.mode)
        if config.enable_audio():
            pipeline_string += ' interaudiosrc name=interaudiosrc ! queue ! audioconvert ! audioresample ! decklinkaudiosink device-number=0'

        self.create_pipeline_from_string(pipeline_string)

    def create_caps_string(self):
        # format=RGB removes the alpha channel which can crash glimagesink
        return #super().create_caps_string(format='UVYV')
