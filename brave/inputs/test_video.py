from brave.inputs.input import Input
from gi.repository import Gst


class TestVideoInput(Input):
    def has_audio(self):
        return False

    def permitted_props(self):
        return {
            'pattern': {
                'type': 'int',
                'default': 0
            },
            'width': {
                'type': 'int',
                'default': 640
            },
            'height': {
                'type': 'int',
                'default': 360
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
        pipeline_string = ('videotestsrc is-live=true name=videotestsrc ! '
                           'videoconvert ! videoscale ! capsfilter name=capsfilter ! '
                           'queue name=queue_into_intervideosink ! intervideosink name=intervideosink')
        if not self.create_pipeline_from_string(pipeline_string):
            return False

        self.intervideosink = self.pipeline.get_by_name('intervideosink')
        self.videotestsrc = self.pipeline.get_by_name('videotestsrc')
        self.capsfilter = self.pipeline.get_by_name('capsfilter')
        if self.intervideosink is None:
            raise Exception('Unable to make test video input - cannot find intervideosink')

        self.create_intervideosrc_and_connections()
        self.handle_updated_props()
        self.set_state(Gst.State.PLAYING)

    def handle_updated_props(self):
        super().handle_updated_props()
        if 'pattern' in self.props:
            self.videotestsrc.set_property('pattern', self.props['pattern'])
