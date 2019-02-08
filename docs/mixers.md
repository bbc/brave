# Mixers
Mixers allow video and audio to be switched and mixed together.

A mixer can have any number of *sources*. Sources can be either [inputs](inputs.md) or the output from other mixers.

[Outputs](outputs.md) can then take a mixer as a source, to deliver its mix elsewhere (e.g. as an RTMP stream, or writing to a file).

Mixers can also have [overlays](overlays.md) applied to them.

There can be any number of mixers. They can be created, updated, and deleted using the [API](api.md). They can also be created at start-up using a [config file](config_file.md).

All together, this allows mixers to be interconnected in interesting ways, for example:

![Example of connected blocks](assets/blocks_example.png "Example of connected blocks")

## Properties
There is only one type of mixer, and it has the following properties:

| Name | Can be set initially? | Can be updated?? | Description | Default value (if not set) |
| ---- | --------------------- | ---------------- | ----------- | -------------------------- |
| `id` | No | No | ID of the mixer. Positive integer. Starts at 1 and increases by 1 for each new mixer. | n/a  |
| `uid` | No | No | Unqiue ID - a string in the format 'mixerX' where X is the ID | n/a  |
| `state` | Yes | Yes | Either `NULL`, `READY`, `PAUSED` or `PLAYING`. [_What are the four states?_](faq.md#what-are-the-four-states) | `PLAYING` |
| `sources` | Yes | Yes (both directly and also via helper API methods `cut_to_source` and `overlay_source`) | An array of inputs and mixers that are the source of this mixer. See below for more. | None |
| `pattern` | Yes | Yes | The pattern used for the background, as an integer. See the [test video](inputs.md#test-video) input type for the list of available patterns. | 0 (SMPTE 100% color bars) |
| `width` and `height` | Yes | Yes | Override of the width and height | The values of `default_mixer_width` and `default_mixer_height` in the [config file](config_file.md). |

### `sources` property

The `sources` properly is an array of dictionaries, for each source that the mixer is currently including. An empty array shows that the mixer has no source. The order of the array has no meaning.

Properties of each source:

| Name | Description | For audio or video sources? | Default |
| ---- | ----------- | --------------------------- | ------- |
| `uid` | the unique ID of the source (e.g. `input1` or `mixer2`) | Both | n/a (required) |
| `in_mix` | `true` iff source is overlayed into mix | Both | `true` |
| `zorder` | The z-order (aka z-index) of the video. Sources with a higher z-order will appear over the sources with a lower z-order. | Video | `1` |
| `width` and `height` | The size of the video. It is useful to set these for 'picture in picture' or 'video wall' use-cases. | Video | If omitted, defaults to the full size of the mixer. |
| `xpos` and `ypos` | The location of the video. | Video | Defaults to 0,0 (i.e. the top-left corner). |
| `volume` | The volume that the input should be mixed at, between 0 (silent) and 1.0 (full volume). | Audio | `1.0` |




