FROM ubuntu:21.04

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -yq \
    build-essential gcc git libffi7 libffi-dev \
    gobject-introspection gstreamer1.0-libav \
    gstreamer1.0-nice gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-tools \
    gir1.2-gst-plugins-bad-1.0 libcairo2-dev \
    libgirepository1.0-dev pkg-config \
    libjpeg-dev python3.9-dev \
    python3-gst-1.0 python3-pip

RUN git clone --depth 1 https://github.com/bbc/brave.git && cd brave && \
    pip3 install -r && \
    mkdir -p /usr/local/share/brave/output_images/

EXPOSE 5000
WORKDIR /brave
CMD ["/brave/brave.py"]
