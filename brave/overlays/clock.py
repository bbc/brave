from brave.overlays.text import TextOverlay


class ClockOverlay(TextOverlay):
    '''
    For doing a text overlay (text graphic).
    '''

    def create_elements(self):
        self.element = self.mixer.add_element('clockoverlay', self)
        self.set_element_values_from_props()
