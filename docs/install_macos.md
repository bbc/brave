# Installing on macOS

This explains how to install Brave on macOS.

First up, make sure you have Homebrew.

## Installing Dependancies

Brave uses from of the newer features of Python. As such we recomend python 3.6 (or higher).

### Managing Dependencies

Brave uses [Pipeenv](https://packaging.python.org/tutorials/managing-dependencies/#managing-dependencies) to manage an isolate its dependencies

If not installed please install using:

`pip install --user pipenv` or `pip3 install --user pipenv`

If your python was installed by brew please use `brew install pipenv`

`pipenv install`

### Errors while installing

Brave uses python-gst which requires the uses of GI. This can be a little tricky to working on OSX with a virtual enviroment. To get around this we can use vext. It requires the libary `libffi`.

Install the libary
`brew install libffi`

Add the location to the env.
`export PKG_CONFIG_PATH="/usr/local/opt/libffi/lib/pkgconfig"`

Try running the install process again.
`pipenv install`

## Installing gstreamer

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

## Changes to brew gstreamer packages
Depending on you brew version some of the options listed above may not be present.

```
brew edit gst-plugins-bad
```
Add the following under `depends_on "orc"`
```
depends_on "libnice" => :recommended
depends_on "rtmpdump" => :recommended
depends_on "srtp" => :recommended
```

The rebuild/install the packages from source. `brew reinstall --build-from-source gst-plugins-bad`

## All done!

Try it out

`pipenv run python3 brave.py`
