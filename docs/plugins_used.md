# GStreamer elements used by Brave

| Element | Module | Where is it used? | Notes |
| ----- | ------- | ------------ | ---- |
| x264 (encoding) | Ugly | RTMP Output |
| Lame (MP3 encoder) | Ugly | NOWHERE! | 
| LibMPEG2 | Ugly | TCP Output - consider removing support for? |
| MPEG Audio Decoder (MAD) | Ugly | Indirectly in the URI input, by `playbin`, for MP3 decode |
| Theora | Ugly | TCP output (as a video encoder, can be swapped for x264) |
| RTMP | Bad | RTMP output, URI Input | This implentation uses AAC audio encoding and h264 video encoding. |
| AAC | Bad | RTMP Output | No licenses or payments are required for a user to stream or distribute content in AAC format (Source: [https://en.wikipedia.org/wiki/Advanced_Audio_Coding](Wikipedia)) |
| SRT | Bad | |
| Nice | Bad | |
| Ogg (audio encoder) | Base | TCP Output | Described as free and open at https://xiph.org/  |
| Vorbis (audio encoder) | Base | TCP output (as an alternative to AC3) | Described as free and open at https://xiph.org/ |


