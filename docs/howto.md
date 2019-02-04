# Brave How-To Guide
This is a how-to guide for some common use-cases of [Brave](../README.md).
See also the [FAQ](faq.md), as well as documentation on the [config file](config_file.md) and [API](api.md).

## How to use Brave as an audio mixer
Brave can be set to handle just audio, and no video. To do so, create a config file containing `enable_video: false`. Then start Brave providing it, for example:

```
echo 'enable_video: false' > /tmp/no_video.yaml
./brave.py -c /tmp/no_video.yaml
```

Here is a richer config file example, setting audio-only and two MP3 inputs:

```
enable_video: false

inputs:
  - type: uri
    uri: "file:///path/to/music1.mp3"
    loop: true
  - type: uri
    uri: "file:///path/to/music2.mp3"
    loop: true

mixers:
  - sources:
    - uid: input1

outputs:
  - type: local
    source: mixer1
```

The mixer has the first input as its source. To switch to the other source, use either the web interface, or the API, e.g.

```
# Switch to input 2:
curl -X POST -d '{"source": "input2"}' http://localhost:5000/api/mixers/1/cut_to_source
```

Mixing two inputs together can be done with `overlay_source` rather than `cut_to_source`.

Seeking to a certain position in (non-live) audio can be done with the `position` property. Multiply the number of seconds position by 1000000000. For example, this will seek to 60 seconds:

```
# Move input 1 to 60 seconds:
curl -X POST -d '{"position": 60000000000}' http://localhost:5000/inputs/1
```

Adding and removing inputs can also be done via the web interface or API.

## How to make a video wall
![Video wall](assets/video_wall.png "Video wall")

A video wall (multiple videos side by side) can be created by resizing video and then declaring where it should appear on the mix.

This can be done as at start-up as a config file, or via the API.

An example config file, to make the image above, can be found in the `config` directory as [../config/video_wall.yaml](video_wall.yaml).

## How to connect a separate GStreamer pipeline to Brave
The best method to output a video (either with or without audio) from GStreamer to Brave is using the TCP protocol. Use the [`tcpserversink`](https://developer.gnome.org/gst-plugins-libs/stable/gst-plugins-base-plugins-tcpserversink.html) element to act as  TCP server; which Brave can then connect to.

The GStreamer process can be running on the same server as Brave, or a different one that has good network connectivity.

Here is an example (a moving ball image and an audio test sound):

```
gst-launch-1.0   \
    videotestsrc pattern=ball ! video/x-raw,width=640,height=360 ! \
    x264enc ! muxer. \
    audiotestsrc ! avenc_ac3 ! muxer. \
    mpegtsmux name=muxer ! queue ! \
    tcpserversink host=0.0.0.0 port=13000 recover-policy=keyframe sync-method=latest-keyframe sync=false
```

To connect Brave to this, create an input of type `tcp_client`. This can be done in the start-up config file, or by REST API, or by the web client. For example, to create an input using the REST API, as a Curl command:

```
curl -X PUT -d '{"type": "tcp_client", "host": "0.0.0.0", "port":13001}' http://localhost:5000/api/inputs
```

Not that this input type assumes the content is delivered as an *MPEG* container. Support for an *Ogg* container is also possible by setting the parameter `container` to `ogg`.

## How to output Brave to a separate GStreamer pipeline
Like above, a TCP connection works well for this, both on the same box and on remote boxes (with good network connections).

First, create a `TCP` output in Brave. This creates a TCP Server from which other GStreamers can connect as clients. You can do this in the config file, or GUI, or as an API call on the command line like this:

```
curl -X PUT -d '{"type": "tcp", "source": "mixer1", "port": 13000}' http://localhost:5000/api/outputs
```

Then, create a GStreamer pipeline that listens to that port. For example, this one will play it locally (audio & video):

```
gst-launch-1.0 tcpclientsrc host=0.0.0.0 port=13000 ! tsdemux name=demux  ! queue2 max-size-time=3000000000 ! decodebin ! autovideosink demux. ! queue2 max-size-time=3000000000 ! decodebin ! autoaudiosink
```

(The large `max-size-time` values help accomodate the key-frame interval.)
