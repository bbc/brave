# Overlays
Overlays allow a graphic or effect to be placed on top of the video. They have no effect on audio.

Overlays can be added to any [input](inputs) or [mixer](mixers.md). This is defined when creating or updating the overlay, by setting the `source` to e.g. `input1` or `mixer2`. Multiple overlays can be added to each input or mixer.

Overlays can be created, updated, and deleted using the [API](api.md). They can also be created at start-up using a [config file](config_file.md).


## Mixer properties
| Name | Required? | Description | Default value (if not set) |
| ---- | --------- | ----------- | -------------------------- |
| `pattern` | No | The pattern used for the background, as an integer. See the [test video](inputs.md#test-video) input type for the list of available patterns. | 0 (SMPTE 100% color bars) |
| `width` and `height` | No | Override of the width and height | The values of `default_mixer_width` and `default_mixer_height` in the [config file](config_file.md). |

### Setting states
A mixer has a state (NULL, READY, PAUSED or PLAYING).
This appears as the `state` field. It can be updated.
To initialise with a state other than PLAYING, set `initial_state` in the `props` section.
