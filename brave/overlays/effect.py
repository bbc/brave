from brave.overlays.overlay import Overlay
from gi.repository import Gst


class EffectOverlay(Overlay):
    '''
    For doing applying a video effect.
    '''

    def permitted_props(self):
        return {
            **super().permitted_props(),
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
                    'radioactv': 'RadioacTV effect',
                    'revtv': 'RevTV effect',
                    'rippletv': 'RippleTV effect',
                    'solarize': 'Solarize',
                    'streaktv': 'StreakTV effect',
                    'vertigotv': 'VertigoTV effect',
                    'warptv': 'WarpTV effect'
                    # Note: quarktv and shagadelictv are removed as they were unreliable in testing
                }
            },
            'visible': {
                'type': 'bool',
                'default': False
            }
        }

    def create_elements(self):
        # The effects filters can mess with the alpha channel.
        # The best solution I've found is to allow it to move into RGBx, then force a detour via RGB
        # to remove the alpha channel, before moving back to our default RGBA.
        # This is done in a 'bin' so that the overlay can be manipulated as one thing.
        desc = ('videoconvert ! %s ! videoconvert ! capsfilter caps="video/x-raw,format=RGB" ! '
                'videoconvert ! capsfilter caps="video/x-raw,format=RGBA"') % self.props['effect_name']
        self.element = Gst.parse_bin_from_description(desc, True)
        self.element.set_name('%s_bin' % self.uid())
        place_to_add_elements = getattr(self.source, 'final_video_tee').parent
        if not place_to_add_elements.add(self.element):
            self.logger.warning('Unable to add effect overlay bin to the source pipeline')
