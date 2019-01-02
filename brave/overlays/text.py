from brave.overlays.overlay import Overlay


class TextOverlay(Overlay):
    '''
    For doing a text overlay (text graphic).
    '''

    def permitted_props(self):
        return {
            **super().permitted_props(),
            'text': {
                'type': 'str',
                'default': 'Default text'
            },
            'valignment': {
                'type': 'str',
                'default': 'bottom',
                'permitted_values': {
                    'top': 'Top',
                    'center': 'Center',
                    'bottom': 'Bottom',
                    'baseline': 'Baseline'
                }
            },
            'visible': {
                'type': 'bool',
                'default': False
            }
        }

    def create_elements(self):
        self.element = self.source.add_element('textoverlay', self, audio_or_video='video')
        self.set_element_values_from_props()

    def set_element_values_from_props(self):
        self.element.set_property('text', self.props['text'])
        self.element.set_property('valignment', self.props['valignment'])
        self.element.set_property('halignment', 'left')
        self.element.set_property('font-desc', 'Sans, 44')
        self.element.set_property('shaded-background', True)
