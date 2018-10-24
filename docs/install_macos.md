# Installing on macOS

This explains how to install Brave on macOS.

First up, make sure you have Homebrew.

## Installing Python

You need 3.6 or higher!

It's worth confirming that the pip matches the version you've installed:

```
pip --version
# Make sure it says "(python 3.6)" (or higher)
```

Now the Python libraries:

```
pip install pyyaml gbulb sanic websockets pytest pillow
```

## Installing gstreamer

First up, dependencies:

```
brew install libnice openssl librsvg libvpx srtp
```

Now on to gsteamer and all of its bits.
Note, versions earlier than 1.14.2 won't work (The .2 point-release fixed WebRTC.)

```
brew install gstreamer
brew install gst-plugins-base --with-theora --with-opus
brew install gst-plugins-good --with-speex --with-cairo --with-gdk-pixbuf --with-libpng --with-libvpx
brew install gst-plugins-bad --with-rtmpdump --with-libvo-aacenc --with-srt --with-libnice --with-gnutls
brew install gst-plugins-ugly  --with-lame --with-x264 --with-libmpeg2 --with-mad --with-theora
brew install gst-libav gst-python
```

## All done!

Try it out

```
./brave.py
```
