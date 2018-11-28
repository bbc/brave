# Installing the 'kvssink' plugin to enable outputting to Kinesis Video Streams
This guide explains how to install [Amazon's Kinesis Video element](https://aws.amazon.com/kinesis/video-streams/) for GStreamer, called 'kvssink'. Doing so allows [Brave](../README.md) to output to a Kinesis video stream.

These instructions are for Ubuntu 18.10. It should be possible to do something similar for MacOS and CentOS. _(Pull requests to add this to the documentation are very welcome!)_

It is assumed that Brave and its dependencies are already installed. [Click here for the guide to installing Brave on Ubuntu.](./install_ubuntu.md)

_NOTE: The current implementation only sends video, not audio, to Kinesis Video._

## STEP 1: Dependencies
We need some additional dependencies in order to compile Kinesis Video:

```
sudo apt-get install libssl-dev libgirepository1.0-dev liblog4cplus-dev libglib2.0-dev libgstreamer-plugins-bad1.0-dev libssl1.1 yasm libltdl7 libfl2 bison cmake libcurl4-openssl-dev libgtest-dev
```

## STEP 2: Build Kinesis Video
These instructions don't use the `install-script` that Amazon provides because it compiles its own GStreamer, whereas we want to use the one already installed.

```
git clone https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp
cd amazon-kinesis-video-streams-producer-sdk-cpp/kinesis-video-native-build

PKG_CONFIG_PATH="/usr/lib/x86_64-linux-gnu/pkgconfig/" cmake CMakeLists.txt
make
```

Test what's been made with:

```
gst-inspect-1.0 ./libgstkvssink.so
```

Check that there are no errors.

Then, manually install the two files into GStreamer's standard location with:

```
sudo cp libgstkvssink.so  libproducer.so /usr/lib/x86_64-linux-gnu/gstreamer-1.0/
```

Now, we can test GStreamer's acceptance of the element with:

```
gst-inspect-1.0 kvssink
```

If that works without error, then we are done!

## STEP 3: Use Brave to output to Kinesis Video

First, [create a Kinesis Video Stream](https://us-west-2.console.aws.amazon.com/kinesisvideo/streams).

You can instruct Brave to output the stream either by adding it to Brave's config file, or via the API (or web GUI). You can add any number of streams, subject to the capacity of your server (and the size of your Amazon bill!)

Here is an example config file to set up one stream:

```
default_outputs:
    - type: kvs
      props:
          stream_name: 'name-of-your-stream'
```

Ensure the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` environment variables are set. This is the same as [used by the AWS comand-line tool](https://docs.aws.amazon.com/cli/latest/userguide/cli-environment.html).

For example, if the above config file was written to `kvs.yaml`, then it could be invocated with:

```
AWS_ACCESS_KEY_ID="XXX" AWS_SECRET_ACCESS_KEY="YYY" ./brave.py -c kvs.yaml
```

Happy streaming!