from brave.inputs.input import Input
from gi.repository import Gst
import brave.config as config


class TestAudioInput(Input):
    def has_video(self):
        return False

    def permitted_props(self):
        return {
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
            config.default_audio_caps() + ' ! interaudiosink name=interaudiosink'

        if not self.create_pipeline_from_string(pipeline_string):
            return False

        self.interaudiosink = self.pipeline.get_by_name('interaudiosink')
        self.audiotestsrc = self.pipeline.get_by_name('audiotestsrc')
        self.create_interaudiosrc_and_connections()
        self.handle_updated_props()
        self.pipeline.set_state(Gst.State.PLAYING)

    def handle_updated_props(self):
        super().handle_updated_props()
        if 'wave' in self.props:
            self.audiotestsrc.set_property('wave', int(self.props['wave']))
        if 'freq' in self.props:
            self.audiotestsrc.set_property('freq', self.props['freq'])
