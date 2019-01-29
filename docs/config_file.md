# Brave config file
[Brave](../README.md) can be configured by config file.
This includes being able to set inputs, mixers, outputs and overlays that are created when Brave starts. It is an alternative to configuring Brave via the [API](api.md).

Brave does not reconsider the config file after it has started. To configure Brave after it has started (e.g. to add another input), use the API.

## Contents

- [Selecting a config file](#selecting-a-config-file)
- [Default config file](#default-config-file)
- [Creating a config file](#creating-a-config-file)
    + [Inputs](#inputs)
    + [Mixers](#mixers)
    + [Outputs](#outputs)
    + [Overlays](#overlays)
    + [Disabling audio or video](#disabling-audio-or-video)
    + [Video width and height](#video-width-and-height)
    + [STUN and TURN servers](#stun-and-turn-servers)



## Selecting a config file
Provide Brave with the config file at startup with the `-c` parameter, e.g.

```
./brave.py -c config/empty.yaml
```

## Default config file
The default config file can be found at `config/default.yaml`.

It creates one mixer, and no inputs or outputs.

## Creating a config file
Config files are written in [YAML](http://yaml.org/), and are simple to create by hand.

The following options can be included in the config file.

### Inputs
Use the `inputs` entry to provide an array of inputs that should be created when Brave starts.

Example:

```
inputs:
     - type: test_video
     - type: uri
       state: PAUSED
       uri: rtmp://184.72.239.149/vod/BigBuckBunny_115k.mov
     - type: image
       zorder: 2
       uri: file:///home/user/images/image.jpg
```

Each input must have a type (e.g. `uri`). Inputs also have a range of other properties. For the full list, see the [inputs](inputs.md) page.


### Mixers
Use the `mixers` entry to provide an array of inputs that should be created when Brave starts. If omitted, one mixer will automatically be created.


Example:

```
mixers:
    - width: 640
      height: 360
      pattern: 6
      source:
          input1: {}
```

Unlike inputs, outputs and overlays, mixers do not have a type. The [mixers](mixers.md) page shows the properties that a mixer can have.

### Outputs
Use `outputs` to define an array of outputs that should be created when Brave starts.

Example (creating four outputs of different types):

```
outputs:
    - type: local
      state: READY
      input_id: 0
      source: mixer1
    - type: image
      source: input1
    - type: tcp
      state: READY
      source: mixer1
    - type: rtmp
      uri: rtmp://domain/path/name
```

Each output must have a type (either 'rtmp', 'tcp', 'image', 'file', 'local', or 'webrtc'). Outputs also have a range of other properties. For the full list, see the [outputs](outputs.md) page.

### Overlays
`overlays` is an array of overlays that should be created when Brave starts.

Example:

```
overlays:
    - type: text
      text: 'I am some text'
      visible: true
      source: mixer1
    - type: effect
      effect_name: warptv
```

Each overlay must have a type (either 'text', 'clock', or 'effect').
Overlays also have a range of other properties. For the full list, see the [overlays](overlays.md) page.

### Disabling audio or video
By default Brave handles video and audio. To disable audio, add the line:

```
enable_audio: false
```

To disable video, add the line:

```
enable_video: false
```

Note that audio and video cannot be enabled/disabled via the API.

### Video width and height
The `default_mixer_height` and `default_mixer_width` values allow you to set the default width and height for a mixer.
The default is a width of 640 and a height of 360.

### STUN and TURN servers
Up to one STUN server and/or one TURN server can be provided. Use the `stun_server` and `turn_server` fields.

Example:

```
stun_server: stun.l.google.com:19302
turn_server: my_name:my_password@my_turn_server_hostname
```
