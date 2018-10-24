from brave.overlays.overlay import Overlay
from gi.repository import Gst
import brave.exceptions


class EffectOverlay(Overlay):
    '''
    For doing applying a video effect.
    '''

    def permitted_props(self):
        return {
            'effect_name': {
                'type': 'str',
                'default': 'edgetv',
                'permitted_values': {
                    'edgetv': 'Edge',
                    'radioactv': 'Radioactive',
                    'agingtv': 'Aging',
                    'warptv': 'Warp'
                }
            },
            'visible': {
                'type': 'bool',
                'default': False
            }
        }

    def create_elements(self):
        self.element = self.mixer.add_element(self.props['effect_name'], self)

    def set_element_values_from_props(self):
        pass

    def update_props(self, props):
        '''
        Stops visiblity change whilst the parent mixer is playing/paused.
        This crashes the pipeline.
        '''
        change_in_visibility_state = False
        if 'visible' in props:
            if hasattr(self, 'visible'):
                change_in_visibility_state = props['visible'] != self.visible
            else:
                change_in_visibility_state = props['visible'] is True

        if (change_in_visibility_state):
            mixer_state = self.mixer.get_state()
            if mixer_state == Gst.State.PLAYING or mixer_state == Gst.State.PAUSED:
                raise brave.exceptions.InvalidConfiguration(
                    'Cannot make effect overlay visible or invisible unless mixer is in READY or NULL state')

        super().update_props(props)
