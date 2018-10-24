from brave.inputs.input import Input
from gi.repository import Gst
import brave.config as config


class UriInput(Input):
    '''
    Handles input via URI.
    This can be anything Playbin accepts, including local files and remote streams.
    '''

    def permitted_props(self):
        return {
            'uri': {
                'type': 'str',
            },
            'volume': {
                'type': 'float',
                'default': 0.8
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
        # Playbin does all the hard work
        if not self.create_pipeline_from_string("playbin uri=\"" + self.props['uri'] + "\""):
            return False

        # playbin appears as 'playsink' (because it's a bin with elements inside)
        self.playsink = self.pipeline.get_by_name('playsink')

        if config.enable_video():
            self.create_video_elements()
        else:
            self._create_fake_video()

        if config.enable_audio():
            self.create_audio_elements()
        else:
            self._create_fake_audio()

        self.handle_updated_props()
        self.set_state(Gst.State.PLAYING)

    def _create_fake_video(self):
        fakesink = Gst.ElementFactory.make('fakesink')
        self.playsink.set_property('video-sink', fakesink)

    def _create_fake_audio(self):
        fakesink = Gst.ElementFactory.make('fakesink')
        self.playsink.set_property('audio-sink', fakesink)

    def create_video_elements(self):
        bin = Gst.parse_bin_from_description(
            f'videoconvert ! videoscale ! capsfilter name=capsfilter ! ' +
            'queue name=queue_into_intervideosink ! intervideosink name=intervideosink', True)

        self.capsfilter = bin.get_by_name('capsfilter')
        self._update_video_filter_caps()

        self.playsink.set_property('video-sink', bin)
        self.intervideosink = bin.get_by_name('intervideosink')
        self.create_intervideosrc_and_connections()

    def create_audio_elements(self):
        bin = Gst.parse_bin_from_description(
            f'audiorate ! audioconvert ! audioresample ! {config.default_audio_caps()} ! ' +
            'queue ! interaudiosink name=interaudiosink', True)
        self.playsink.set_property('audio-sink', bin)
        self.interaudiosink = bin.get_by_name('interaudiosink')
        self.create_interaudiosrc_and_connections()

    def update(self, updates):
        super().update(updates)

        # Special case: allow seeking
        if self.has_video() and 'position' in updates:
            try:
                new_position = float(updates['position'])
                if self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, new_position):
                    self.logger.debug('Successfully updated position to %s' % new_position)
                else:
                    self.logger.warn('Unable to est position to %s' % new_position)
            except ValueError:
                self.logger.warn('Invalid position %s provided' % updates['position'])

    def get_input_cap_props(self):
        '''
        Parses the caps that arrive from the input, and returns them.
        This allows the height/width/framerate/audio_rate to be retrieved.
        '''

        elements = {}
        if hasattr(self, 'intervideosink'):
            elements['video'] = self.intervideosink
        if hasattr(self, 'interaudiosink'):
            elements['audio'] = self.interaudiosink

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
            if structure.has_field('channels'):
                props[audioOrVideo + '_channels'] = structure.get_int('channels').value
            if structure.has_field('rate'):
                props[audioOrVideo + '_rate'] = structure.get_int('rate').value

        return props
