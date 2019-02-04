from brave.inputs.input import Input
from gi.repository import Gst
import brave.config as config


class DecklinkInput(Input):
    '''
    Handles input via a deckoink card/device.
    This can allow SDI/HDMI singals to be localy mixed with brave
    '''
    def permitted_props(self):
        return {
            **super().permitted_props(),
            'device': {
                'type': 'int',
                'default': 0,
            },
            'connection': {
                'type': 'int',
                'default': 1,
            },
            'mode': {
                'type': 'int',
                'default': 17,
            },
            'width': {
                'type': 'int',
                'default': 1280
            },
            'height': {
                'type': 'int',
                'default': 720
            }
        }

    def create_elements(self):
        #TODO: Audio is currently lcoked to HDI/HDMI mode may need to figure a btter way to auto select the best one
        if not self.create_pipeline_from_string('decklinkvideosrc'
                                        ' device-number=' + str(self.device) +
                                        ' connection=' + str(self.connection) +
                                        ' mode=' + str(self.mode) +
                                        ' ! videoconvert ! '
                                        + self.default_video_pipeline_string_end() +
                                        ' decklinkaudiosrc device-number=' + str(self.device) + ' connection=1 ! audioconvert'
                                        + self.default_audio_pipeline_string_end()):
            return False

        self.intervideosink = self.pipeline.get_by_name('intervideosink')
        self.final_video_tee = self.pipeline.get_by_name('final_video_tee')
        self.final_audio_tee = self.pipeline.get_by_name('final_audio_tee')
        self.handle_updated_props()

    def get_input_cap_props(self):
        '''
        Parses the caps that arrive from the input, and returns them.
        This allows the height/width/framerate/audio_rate to be retrieved.
        '''
        elements = {}
        if hasattr(self, 'intervideosink'):
            elements['video'] = self.intervideosink

        props = {}
        for (audioOrVideo, element) in elements.items():
            if not element:
                return
            caps = element.get_static_pad('sink').get_current_caps()
            if not caps:
                return
            size = caps.get_size()
            if size == 0:
                return

            structure = caps.get_structure(0)
            props[audioOrVideo + '_caps_string'] = structure.to_string()
            if structure.has_field('framerate'):
                framerate = structure.get_fraction('framerate')
                props['framerate'] = framerate.value_numerator / framerate.value_denominator
            if structure.has_field('height'):
                props['height'] = structure.get_int('height').value
            if structure.has_field('width'):
                props['width'] = structure.get_int('width').value

        return props
