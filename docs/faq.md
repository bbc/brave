# Frequently Asked Questions

## What is Brave?
[Brave](../README.md) is a wrapper around parts of [GStreamer](http://gstreamer.freedesktop.org/) that allows live audio and video streams to be handled via a RESTful API. Content can be received, mixed, monitored, and sent to other destinations. It allows multiple 'blocks' - inputs, outputs, mixers and overlays - to be created and connected. Brave is designed to work remotely, such as on the cloud.

## What do the four states (NULL, READY, PAUSED, PLAYING) mean?
Inputs, mixers and outputs are always in one of four states. These states are the same as [GStreamer's states](https://gstreamer.freedesktop.org/documentation/design/states.html).

| Name | Meaning |
| ---- | ------- |
| `NULL` | Block is not initialised, or has had an error. |
| `READY` | Block it not currently playing. |
| `PAUSED` | Block has connected and the content is paused. |
| `PLAYING` | Block is successfully playing content. |


## Can support be added for another input or output type/protocol?
Because Brave is based on GStreamer, it can only support what GStreamer supports. It cannot act as an RTMP server, for example, because there is no GStreamer element that can do that.

Where GStreamer plugins do exist, adding them as a new form of input or output should be relatively easy. Start with an existing one (in the `brave/inputs` and `brave/outputs` directories) and clone it. Then please raise as a pull request. Or you could [request it by raising an issue](https://github.com/bbc/brave/issues).

## I've found a bug
Please [raise an issue in GitHub](https://github.com/bbc/brave/issues).

## Can I contribute?
Yes, pull requests are welcome.
Please ensure the tests are passing and the flake8 linting is returning success first. (Information on these can be found in the [README](../readme.md)).
