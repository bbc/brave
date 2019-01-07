# Brave config file
[Brave](../README.md) can be configured by config file.
This includes being able to set inputs, mixers, outputs and overlays that are created when Brave starts. It is an alternative to configuring Brave via the API.

Brave does not reconsider the config file after it has started. To configure Brave after it has started (e.g. to add another input), use the API.

## Selecting a config file
Provide Brave with the config file at startup with the `-c` parameter, e.g.

```
./brave.py -c config/example_empty.yaml
```

## Default config file
The default config file can be found at `config/default.yaml`.

It creates one mixer, and no inputs or outputs.

## Custom config files
Config files are written in [YAML](http://yaml.org/), and are simple to create by hand.

The following options can be included in the config file.

### `default_inputs`
Use the `default_inputs` entry to provide an array of inputs that should be created when Brave starts.

Example:

```
default_inputs:
     - type: uri
       props:
           initial_state: PAUSED
           uri: rtmp://184.72.239.149/vod/BigBuckBunny_115k.mov
     - type: image
       props:
           zorder: 2
           uri: file:///home/user/images/image.jpg
```

Each input must have a type (either `uri`, `image`, `html`, `test_video`, or `test_audio`)

Each input can then, optionally, have `props` containing key-values pairs of the properties of that input. Available properties vary per input. Common ones include:

* `uri` - of the content to display. (Does not exist for `test_video` or `test_audio`)
* `zorder` - the ordering that that input should appear when mixed
* `intial_state` - the state that the input should enter. Permitted values: 'PLAYING', 'PAUSED', 'READY', 'NULL. Defaults to PLAYING.


### `default_mixers`
Use the `default_mixers` entry to provide an array of inputs that should be created when Brave starts. If omitted, one mixer will automatically be created.


Example:

```
default_mixers:
    - props:
        width: 640
        height: 360
        pattern: 6
```

Unlike inputs and outputs, mixers do not have a type.

Properties, all optional, are:

* `width` - if not set, defaults to `default_mixer_height` (see below)
* `height` - if not set, defaults to `default_mixer_width` (see below)
* `pattern` - bettween 0 and 24, matching the pattern list [here](https://gstreamer.freedesktop.org/data/doc/gstreamer/head/gst-plugins-base-plugins/html/gst-plugins-base-plugins-videotestsrc.html#GstVideoTestSrcPattern.members). If not set, defaults to 0 (SMPTE test pattern)
* `intial_state` - the state that the mixer should enter. Permitted values: 'PLAYING', 'PAUSED', 'READY', 'NULL. Defaults to PLAYING.

### `default_outputs`
`default_outputs` is an array array of inputs that should be created when Brave starts.

Example (creating four outputs of different types):

```
default_outputs:
    - type: local
      props:
          initial_state: READY
          input_id: 0
    - type: image
    - type: tcp
      props:
          initial_state: READY
          mixer_id: 1
    - type: rtmp
      props:
          uri: rtmp://domain/path/name
```

Each output must have a type (either 'rtmp', 'tcp', 'image', 'file', 'local', or 'webrtc').

Each output can then, optionally, have `props` containing key-values pairs of the properties of that input. Available properties vary per output. All outputs have the following properties:

* `width` - the width of the output.
* `height` - the height of the output.
* `intial_state` - the state that the output should enter. Permitted values: 'PLAYING', 'PAUSED', 'READY', 'NULL. Defaults to PLAYING.
* `mixer_id` and `input_id` - provide one of these to define what the source of the output should be. If neither are set, the first mixer (mixer 0) is assumed. Inputs and mixers are given IDs based on their order in the config file, starting at 0. For example, `input_id: 2` would set the output's source to be the third input defined.

### `default_overlays`
`default_overlays` is an array of overlays that should be created when Brave starts.

Example:

```
default_overlays:
    - type: text
      props:
          text: 'I am some text'
          visible: true
    - type: effect
      props:
	I      effect_name: warptv
```

Each overlay must have a type (either 'text', 'clock', or 'effect').

Each overlay can then, optionally, have `props` containing key-values pairs of the properties of that input. Available properties vary per overlay type, and include:

* `visible` - whether the overlay is currently visible. Can be either `true` or `false`.
* `effect_name` - only for the `effect` type. Valid values include `agingtv`, `warptv`, and `rippletv`. See the full list in the code [here](../brave/overlays/effect.py).

### `enable_video` and `enable_audio`
By default Brave handles video and audio. To disable audio, add the line:

```
enable_audio: false
```

To disable video, add the line:

```
enable_video: false
```

Note that audio and video cannot be enabled/disabled via the API.

### `default_mixer_height` and `default_mixer_width`
These allow you to set the default width and height for a mixer.
The default is a width of 640 and a height of 360.

### `stun_server` and `turn_server`
Up to one STUN server and/or one TURN server can be provided. Example:

```
stun_server: stun.l.google.com:19302
turn_server: my_name:my_password@my_turn_server_hostname
```
