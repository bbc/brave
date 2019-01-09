from brave.inputs.input import Input
import brave.config as config


class TestAudioInput(Input):
    def has_video(self):
        return False

    def permitted_props(self):
        return {
            **super().permitted_props(),
            'freq': {
                'type': 'int',
                'default': 440
            },
            'wave': {
                'type': 'int',
                'default': 0
            },
            'volume': {
                'type': 'float',
                'default': 0.8
            }
        }

    def create_elements(self):
        pipeline_string = 'audiotestsrc is-live=true name=audiotestsrc volume=0.2 ! ' + \
            config.default_audio_caps() + self.default_audio_pipeline_string_end()

        self.create_pipeline_from_string(pipeline_string)

        self.final_audio_tee = self.pipeline.get_by_name('final_audio_tee')
        self.audiotestsrc = self.pipeline.get_by_name('audiotestsrc')

    def handle_updated_props(self):
        super().handle_updated_props()
        if hasattr(self, 'wave'):
            self.audiotestsrc.set_property('wave', int(self.wave))
        if hasattr(self, 'freq'):
            self.audiotestsrc.set_property('freq', self.freq)
