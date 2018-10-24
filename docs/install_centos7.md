# Installing on CentOS 7

This explains how to install GStreamer 1.14 and Python 3.6 on CentOS 7.

## Dependencies

```
sudo yum -y install gtk-doc glib2 glib2-devel speex speex-devel wget pygobject3-devel  cairo cairo-devel cairo-gobject cairo-gobject-devel libnotify-devel libnotify libjpeg-turbo-devel nginx pango-devel orc-devel libvorbis-devel libtheora-devel libxml2-devel openssl-devel libsoup-devel mpg123-libs webrtc-audio-processing-devel gnutls-devel libvpx-devel librsvg2-devel
```

Not sure about whether `libtool-ltdl-devel` is required!

### Automake 1.14

This isn't in Yum.
Instead, follow the instructions at https://techglimpse.com/install-update-autoconf-linux-tutorial/

## Python 3.6

This is well described at https://janikarhunen.fi/how-to-install-python-3-6-1-on-centos-7.html

## Set lib directories

Set these:

```
export LD_LIBRARY_PATH=/usr/lib64/
export PKG_CONFIG_PATH=/usr/lib64/pkgconfig/
```


## nasm 2.13

Required to build x264

```
cd /etc/yum.repos.d/
sudo wget https://www.nasm.us/nasm.repo
cd
yum clean all
sudo yum install nasm
```


## x264

```
wget ftp://ftp.videolan.org/pub/x264/snapshots/last_x264.tar.bz2
tar xf last_x264.tar.bz2
cd x264-snapshot-*
./configure --enable-shared --enable-static --libdir=/usr/lib64
make
sudo make install
```

## RTMP

```
git clone git://git.ffmpeg.org/rtmpdump
cd rtmpdump
make SYS=posix XCFLAGS="-fPIC"
sudo make install

# Hacky next step, as rtmpdump Makefile does not allow lib dir override:
sudo cp /usr/local/lib/librtmp* /usr/lib64/
sudo cp /usr/local/lib/pkgconfig/librtmp* /usr/lib64/pkgconfig/
```

## openh264

```
git clone https://github.com/cisco/openh264.git
cd openh264
make OS=linux ARCH=x86_64
sudo make install

# Hacky next step, as openh264 Makefile does not allow lib dir override:
sudo cp /usr/local/lib/libopenh264.* /usr/lib64/
sudo cp /usr/local/lib/pkgconfig/openh264.pc /usr/lib64/pkgconfig/
```


## libnice

This is required for WebRTC support.

```
wget https://nice.freedesktop.org/releases/libnice-0.1.14.tar.gz
tar xf libnice-0.1.14.tar.gz
cd libnice-0.1.14
./configure --libdir=/usr/lib64 && make && sudo make install

# Double-check it's in /usr/lib64/libnice.* not /usr/local/lib/libnice.*
```


## Opus

The Opus audio codec is required for WebRTC.
There is a version in yum, so this source compile is probably not essential.
But it does get you a newer version (with better quality encodings).


```
wget https://archive.mozilla.org/pub/opus/opus-1.2.1.tar.gz
tar xf opus-1.2.1.tar.gz
opus-1.2.1
./configure --libdir=/usr/lib64
make && sudo make install
```


## Faac

No sign of this in Centos 7 Yum.
I've gone for the latest version at the time of writing (1.19.9.2). There is a problem with building 1.28.

```
wget http://downloads.sourceforge.net/faac/faac-1.29.9.2.tar.gz
tar xf faac-1.29.9.2.tar.gz
cd faac-1.29.9.2
./configure --libdir=/usr/lib64
make && sudo make install
```


## SRT

This is optional, if you wish to use SRT. It's definitely not available via yum (don't get confused with SRTP!)

Instructions are at  https://github.com/Haivision/srt


## GStreamer

It's important to install 1.14 (or later). Otherwise WebRTC won't work.


### The main GStreamer modules (x6)

Install gstreamer core:

```
export REPO_NAME=gstreamer
export GSTREAMER_VERSION=1.14.3
git clone git://anongit.freedesktop.org/git/gstreamer/$REPO_NAME
cd $REPO_NAME
git checkout tags/$GSTREAMER_VERSION
# Or: git checkout remotes/origin/1.14
libtoolize
./autogen.sh --disable-gtk-doc --enable-introspection=yes --libdir=/usr/lib64
make
sudo make install
```

Now repeat the above, setting `REPO_NAME` to be each of

* `gst-plugins-base`
* `gst-plugins-good`
* `gst-plugins-ugly`
* `gst-libav`


### gst-plugins-bad

This one has some specific autogen commands

```
export REPO_NAME=gst-plugins-bad
export GSTREAMER_VERSION=1.14.3
git clone git://anongit.freedesktop.org/git/gstreamer/$REPO_NAME
cd $REPO_NAME
git checkout tags/$GSTREAMER_VERSION
# Or: git checkout remotes/origin/1.14
libtoolize
./autogen.sh --disable-gtk-doc --enable-introspection=yes --libdir=/usr/lib64 --enable-rtmp=yes --enable-dash=yes --enable-webrtc=yes --enable-srt=yes --enable-faac=yes
make
sudo make install
```


## Compile and install gst-python

```
git clone git://anongit.freedesktop.org/gstreamer/gst-python
cd gst-python
git checkout tags/$GSTREAMER_VERSION
libtoolize
PYTHON=python3.6 ./autogen.sh --prefix=/usr
make
sudo make install
```


## Install Python libraries

Simply:

```
sudo pip3.6 install pyyaml gbulb sanic websockets pytest psutil
```


## Then try brave

Always remember to specify the python version:

```
python3.6 brave.py
```


## To set up nginx

Update Nginx to enable port 443 (by uncommenting the bottom half.)

Then add a self-signed cert with:

```
sudo mkdir -p /etc/pki/nginx/private
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/pki/nginx/private/server.key -out /etc/pki/nginx/server.crt
```

Give nginx permission to make the proxy call:

```
sudo setsebool -P httpd_can_network_connect 1
```


## Troubleshooting

### Error message `ValueError: Namespace Gst not available`

This is when Gst-Python cannot find GStreamer. Check:

* Is the core 'gstreamer' library installed as above?
* Was is configured with `--enable-introspection=yes`?
* Is it definitely in `/usr/lib64/gstreamer-1.0` ?


### A certain element is not installed

Use `gst-inspect-1.0` to see what's installed. e.g.

```
gst-inspect-1.0 | grep opus
```

You can also inspect what's installed at a file level, e.g.

`gst-inspect-1.0 /usr/lib64/gstreamer-1.0/libgstopusparse.so`

If it's missing, it's probably because dependencies are missing. Google to discover which package it belongs (base/good/bad/ugly). Then capture the output of `autogen.sh` to see what's missing.


## Appendix - references

This was very useful: https://gist.github.com/Swap-File/ea4b7a4739ca8c859bd7c3c3d8b087e6
