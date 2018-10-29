from brave.overlays.overlay import Overlay


class EffectOverlay(Overlay):
    '''
    For doing applying a video effect.
    '''

    def permitted_props(self):
        return {
            'mixer_id': {
                'type': 'int',
                'default': 0
            },
            'effect_name': {
                'type': 'str',
                'default': 'edgetv',
                'permitted_values': {
                    'agingtv': 'AgingTV effect',
                    'burn': 'Burn',
                    'chromium': 'Chromium',
                    'dicetv': 'DiceTV effect',
                    'dilate': 'Dilate',
                    'dodge': 'Dodge',
                    'edgetv': 'EdgeTV effect',
                    'exclusion': 'Exclusion',
                    'optv': 'OpTV effect',
                    'quarktv': 'QuarkTV effect',
                    'radioactv': 'RadioacTV effect',
                    'revtv': 'RevTV effect',
                    'rippletv': 'RippleTV effect',
                    'shagadelictv': 'ShagadelicTV',
                    'solarize': 'Solarize',
                    'streaktv': 'StreakTV effect',
                    'vertigotv': 'VertigoTV effect',
                    'warptv': 'WarpTV effect'
                }
            },
            'visible': {
                'type': 'bool',
                'default': False
            }
        }

    def create_elements(self):
        self.element = self.mixer().add_element(self.props['effect_name'], self)

    def set_element_values_from_props(self):
        pass
