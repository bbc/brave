from brave.overlays.text import TextOverlay


class ClockOverlay(TextOverlay):
    '''
    For doing a text overlay (text graphic).
    '''

    def create_elements(self):
        self.element = self.source.add_element('clockoverlay', self, audio_or_video='video')
        self.set_element_values_from_props()
