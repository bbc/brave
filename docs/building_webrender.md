#WebRenderSrc (WIP)

We also ship an experimental Cef render which can be given an URL and renders it to a video src. The intention to use this for HTML grahics

## Building
The building tools require cmake which can be install with `brew install cmake`. To compile on MacOS place make sure you have xcode and xcode-cli tools install and available on the `$PATH`
```
cd gst-WebRenderSrc
CC=clang CXX=clang++ cmake .
make
make install
```

## Dependencies
The make script will try and fetch and lovate as many of the required libs as possible before building. This package uses a precompiled CEF build make available with thanks to spotify.

If you have an error on macosx64 on the lines of `ld: library not found for -lintl` This may be due to the compiler requring gettext.
To install on MacOS use brew.

```
brew install gettext
brew link --force gettext
```

This package also requires libcef to function correctly on win and linux it is realvilty simple to link to. On macOS cef was desgined to function with app bundling.

To get around this issue in a _hacky_ way we will just move the cef frameworks to `/usr/local/Frameworks` and use the linking tool to change were the plugin can find the refrences using `install_name_tool`.

TODO: Make this lees hacky or figure out how the bundling method works with .so objects 🤔

```
cp "/Frameworks/Chromium Embedded Framework.framework/Chromium Embedded Framework" "/usr/local/Frameworks/Chromium Embedded Framework.framework/Chromium Embedded Framework"

install_name_tool -change "@rpath/Frameworks/Chromium Embedded Framework.framework/Chromium Embedded Framework" "/usr/local/Frameworks/Chromium Embedded Framework.framework/Chromium Embedded Framework" ./src/Release/libwebrendersrc.so
``