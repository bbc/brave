# Inputs
Inputs allow you to source content (e.g. from an RTMP stream or a file.) There can be any number of inputs, and can be created, updated, and deleted using the [API](api.md). They can also be created at start-up using a [config file](config_file.md).

Each input can be connected to any number of [mixers](mixers.md) or [outputs](outputs.md).

Inputs can also have [overlays](overlays.md) applied to them.

## Common properties

All inputs have the following properties:

| Name | Can be set initially? | Can be updated?? | Description | Default value (if not set) |
| ---- | --------------------- | ---------------- | ----------- | -------------------------- |
| `type` | Yes | No | The input type, e.g. `uri`. | N/A - **REQUIRED** |
| `state` | Yes | Yes | Either `NULL`, `READY`, `PAUSED` or `PLAYING`. [_What are the four states?_](faq.md#what-are-the-four-states) | `PLAYING` |
| `desired_state` | No (Use `state`) | No (Use `state`) | Set to state that the user has requested, when it has not yet been reached. |


## Input types
Brave currently supports these input types:

- [uri](#uri)
- [image](#image)
- [test_video](#test_video)
- [test_audio](#test_audio)

(An experimental fifth type, _HTML_, is not documented yet.)

### uri
The `uri` input type uses GStreamer's `playbin` element to accept a wide variety of input types can can be accessed via a URI. These can be live streams or recorded content. These can be video or audio (e.g. music). Examples include:

* An RTMP stream (URI starting with `rtmp://`)
* A HLS stream (HTTP(S) URI pointing at a HLS manifest)
* A remote file (e.g. `https://myserver.com/video.mp4`)
* A local file (e.g. `file:///home/user/song.mp3`)

The types of content accepted will depend, in part, on which decoders and GStreamer elements that are installed.

Note that this type does not as a server. Content must be 'pulled' from another place. For example, if you had a video source that wanted to send RTMP, you'd require an RTMP server to accept this so that Brave could then read it.

### Properties
In addition to the common properties above, this input type also has the following:

| Name | Can be set initially? | Can be updated?? | Description | Default value (if not set) |
| ---- | --------------------- | ---------------- | ----------- | -------------------------- |
| `id` | No | No | ID of the input. Positive integer. Starts at 1 and increases by 1 for each new input. | n/a  |
| `uid` | No | No | Unqiue ID - a string in the format 'inputX' where X is the ID | n/a  |
| `uri` | Yes | No | The URI of the image | n/a - REQUIRED PROPERTY |
| `width` and `height` | Yes | Yes | Override of the width and height (both non-negative integers) | None (will appear full-screen on mixer/output) |
| `volume` | Yes | Yes | The volume. Floating point value, between 0 (silent) and 1 (full volume). | 0.8 |
| `position` | No (should be possible in a future release) | Yes | The current position (time) of the media. It's in nanoseconds (so divide the number by 1000000000 to turn into seconds.) | 0 |
| `duration` | No (should be possible in a future release) | Yes | The duration of the content, or `-1` if there is no duration (e.g. for a live stream). | The asset duration, or `-1` |


### image
The `image` input type is for when an image (JPEG, PNG, etc.) should be displayed on the video. This can be used as a way of adding graphics. PNG images with transparent backgrounds are supported (and work well when overlayed on video). Animated GIFs are not supported.

The image should be available as a file, and described as a URI. This means it can be local (e.g. `file:///home/user/pic.jpg`) or remote (e.g. `https://myserver.com/pic.jpg`).

#### Properties
In addition to the common properties above, this input type also has the following:

| Name | Can be set initially? | Can be updated?? | Description | Default value (if not set) |
| ---- | --------------------- | ---------------- | ----------- | -------------------------- |
| `uri` | Yes | No | The URI of the image | n/a - REQUIRED PROPERTY |
| `width` and `height` | Yes | Yes | Override of the width and height | None (will appear full-screen on mixer/output) |

### test_video
A video test source, which is useful for checking connections, or to provide a background. There is no audio.
(This input type makes use of the [videotestsrc](https://gstreamer.freedesktop.org/data/doc/gstreamer/head/gst-plugins-base-plugins/html/gst-plugins-base-plugins-videotestsrc.html) GStreamer element).


Supply a `pattern` property to choose from 25 patterns:

- (0): smpte            - SMPTE 100% color bars
- (1): snow             - Random (television snow)
- (2): black            - 100% Black
- (3): white            - 100% White
- (4): red              - Red
- (5): green            - Green
- (6): blue             - Blue
- (7): checkers-1       - Checkers 1px
- (8): checkers-2       - Checkers 2px
- (9): checkers-4       - Checkers 4px
- (10): checkers-8       - Checkers 8px
- (11): circular         - Circular
- (12): blink            - Blink
- (13): smpte75          - SMPTE 75% color bars
- (14): zone-plate       - Zone plate
- (15): gamut            - Gamut checkers
- (16): chroma-zone-plate - Chroma zone plate
- (17): solid-color      - Solid color
- (18): ball             - Moving ball
- (19): smpte100         - SMPTE 100% color bars
- (20): bar              - Bar
- (21): pinwheel         - Pinwheel
- (22): spokes           - Spokes
- (23): gradient         - Gradient
- (24): colors           - Colors

#### Properties
In addition to the common properties above, this input type also has the following:

| Name | Can be set initially? | Can be updated?? | Description | Default value (if not set) |
| ---- | --------------------- | ---------------- | ----------- | -------------------------- |
| `pattern` | Yes | Yes | The number of the pattern (between 0 and 24, as listed above) | 0 (SMPTE 100% color bars) |
| `width` and `height` | Yes | Yes | Override of the width and height | None (will appear full-screen on mixer/output) |

### test_audio
An audio test input. This is useful for testing/checking your setup. There is no video.
(This input type makes use of the [audiotestsrc](https://gstreamer.freedesktop.org/data/doc/gstreamer/head/gst-plugins-base-plugins/html/gst-plugins-base-plugins-audiotestsrc.html) GStreamer element).

Supply a `wave` property to choose from 13 wave options:

- (0): sine             - Sine
- (1): square           - Square
- (2): saw              - Saw
- (3): triangle         - Triangle
- (4): silence          - Silence
- (5): white-noise      - White uniform noise
- (6): pink-noise       - Pink noise
- (7): sine-table       - Sine table
- (8): ticks            - Periodic Ticks
- (9): gaussian-noise   - White Gaussian noise
- (10): red-noise        - Red (brownian) noise
- (11): blue-noise       - Blue noise
- (12): violet-noise     - Violet noise

#### Properties
In addition to the common properties above, this input type also has the following:

| Name | Can be set initially? | Can be updated?? | Description | Default value (if not set) |
| ---- | --------------------- | ---------------- | ----------- | -------------------------- |
| `freq` | Yes | Yes | Frequency of the test sound, in Hz. Provide as an integer. | 440 (Hz) |
| `wave` | Yes | Yes | The number of the wave (between 0 and 13, as listed above) | 0 (sine) |
| `volume` | Yes | Yes | The volume. Floating point value, between 0 (silent) and 1 (full volume). | 0.8 |
