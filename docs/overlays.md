# Overlays
Overlays allow a graphic or effect to be placed on top of the video. They have no effect on audio.

Overlays can be added to any [input](inputs.md) or [mixer](mixers.md). This is defined when creating or updating the overlay, by setting the `source` to e.g. `input1` or `mixer2`. Multiple overlays can be added to each input or mixer.

Overlays can be created, updated, and deleted using the [API](api.md). They can also be created at start-up using a [config file](config_file.md).

## Common properties

All types of overlays have the following properties:

| Name | Can be set initially? | Can be updated?? | Description | Default value (if not set) |
| ---- | --------------------- | ---------------- | ----------- | -------------------------- |
| `id` | No | No | ID of the overlay. Positive integer. Starts at 1 and increases by 1 for each new mixer. | n/a  |
| `uid` | No | No | Unqiue ID - a string in the format 'overlayX' where X is the ID | n/a  |
| `type` | Yes | No | The name of the overlay type, e.g. `text`. | N/A - **REQUIRED** |
| `visible` | Yes | Yes | Boolean. Whether the effect is visible on the video. | False |
| `source` | Yes | Yes (but only in the NULL or READY states) | The `uid` of the input or mixer that the overlay is overlaying. e.g. `mixer1` | The mixer with the lowest ID (usually `mixer1`) |

## Overlay types
Brave currently supports these overlay types:

- [text](#text)
- [clock](#clock)
- [effect](#effect)

### text
Shows text on the screen.

### Additional properties
In addition to the common properties defined above, this overlay also has:

| Name | Can be set initially? | Can be updated?? | Description | Default value (if not set) |
| ---- | --------------------- | ---------------- | ----------- | -------------------------- |
| `text` | Yes | Yes | The text to display. | Empty string |
| `valignment` | Yes | Yes | The vertical alignment of the text. Can be `top`, `center` or `bottom`. | Empty string |


### clock
The `clock` overlay shows the current time, and also any other text provided in the `text` property. It is a useful overlay to determine if there is any delay in the video.

This overlay shares the same properties as the `text` overlay.


### effect
The `effect` overlay allows a range of video transformation effects to be applied.

This overlay has one additional property - `effect_name` - which can be set to one of the following values:

* `agingtv`: AgingTV (adds age to video input using scratches and dust)
* `burn`: Burn (adjusts the colors in the video)
* `chromium`: Chromium (breaks the colors of the video)
* `dicetv`: DiceTV (\'Dices\' the screen up into many small squares)
* `dilate`: Dilate (copies the brightest pixel around)
* `dodge`: Dodge (saturates the colors in the video)
* `edgetv`: EdgeTV effect
* `exclusion`: Exclusion (exclodes the colors in the video)
* `optv`: OpTV (Optical art meets real-time video)
* `radioactv`: RadioacTV (motion-enlightment)
* `revtv`: RevTV (A video waveform monitor for each line of video)
* `rippletv`: RippleTV (ripple mark effect on the video)
* `solarize`: Solarize (tunable inverse in the video)
* `streaktv`: StreakTV (makes after images of moving objects)
* `vertigotv`: VertigoTV (blending effector with rotating and scaling)
* `warptv`: WarpTV (goo\'ing of the video)

If omitted, the default is `edgetv`.