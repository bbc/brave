# Brave API

[Brave](../README.md) has a RESTful JSON API that allows you to dynamically add and remove inputs, mixers, outputs and overlays. It is designed to be fast, simple, and stateless.

(You can also configure Brave at startup using the [YAML config file](config_file.md)).

A [websocket connection](#websocket) is also available for when your client wishes to be notified of updates (e.g. when an input ends).

## Contents
- [Where to find the API](#where-to-find-the-api)
- [General](#general-api-calls)
- [Inputs](#Inputs)
- [Mixers](#mixers)
- [Outputs](#Outputs)
- [Overlays](#overlays)
- [Websocket](#websocket)

## Where to find the API
The API is found at the same port as the web interface, on the `/api` path. It defaults to port 5000, which the example URLs below assume. Change the port either with the `PORT` environment variable, or by setting `api_port` in the config file.

## General API calls

### Get details on all inputs/outputs/mixers/overlays
Retrieve information on all created items (blocks). The response is a map (dictonary) with four keys for the four types (`inputs`, `outputs`, `mixers`, and `overlays`). If you only need one of these types, use the relevant call for that, e.g.  [`/api/inputs`](#get-all-inputs).

- Path: `/api/all`
- Method: `GET`
- Local URL example: [http://localhost:5000/api/all](http://localhost:5000/api/all)

#### Command-line curl example
```
curl http://localhost:5000/api/all
```

#### Example response
```
{
  "inputs": [
    {
      "has_audio": true,
      "has_video": true,
      "uid": "input1",
      "volume": 0.8,
      "uri": "rtmp://ec2-34-249-249-218.eu-west-1.compute.amazonaws.com:8001/live/go1",
      "state": "READY",
      "id": 1,
      "type": "uri",
      "position": -1,
      "connection_speed": 0,
      "buffer_size": -1,
      "buffer_duration": 3000000000
    }
  ],
  "overlays": [],
  "outputs": [
    {
      "has_audio": true,
      "has_video": true,
      "uid": "output1",
      "width": 640,
      "height": 360,
      "state": "PLAYING",
      "id": 1,
      "type": "local",
      "source": "mixer1"
    }
  ],
  "mixers": [
    {
      "has_audio": true,
      "has_video": true,
      "uid": "mixer1",
      "width": 640,
      "height": 360,
      "pattern": 0,
      "state": "PLAYING",
      "id": 1,
      "type": "mixer",
      "sources": [
        {
          "uid": "input1",
          "id": 1,
          "block_type": "input",
          "in_mix": true
        }
      ]
    }
  ]
}
```

### Restart Brave
Restart Brave. This will reset all settings and connections.

- Path: `/api/restart`
- Method: `POST`
- Request body: JSON, containing one key `config` set to either `original` or `current`.
If set to `original`, restarts Brave with the orginal config file from when the current process started. If `current`, restarts Brave with the current config, so that the exact setup can be recreated.

#### Command-line curl example
```
curl -X POST -d {'config':'original'}  http://localhost:5000/api/restart
```

### Get config as YAML
Get the current config in YAML. This can then be saved as a file which is
accepted by another Brave instance on startup.

- Path: `/api/config/current.yaml`
- Method: `GET`

#### Command-line curl example
```
curl http://127.0.0.1:5000/api/config/current.yaml > /tmp/config.yaml
# Which you could then pass to Brave on another occasion, e.g.
brave.py -c /tmp/config.yaml
```

## Inputs
Inputs allow you to source content (e.g. from an RTMP stream or a file.) There can be any number of inputs, and they can be created, updated, and deleted. [Read more about input types.](./inputs.md)


### Get all inputs
Get an array of all inputs.

- Path: `/api/inputs`
- Method: `GET`

#### Command-line curl example
```
curl http://localhost:5000/api/inputs
```

### Create an input
Create a new input. There are different types of inputs. You must specify a `type`, and [depending on the input type chosen](./inputs.md), there may be other required or optional parameters.

- Path: `/api/inputs`
- Method: `PUT`
- Request body: JSON, containing a dictionary with the required parameters.

#### Command-line curl example
```
curl -X PUT -d '{"type": "test_video"}' http://localhost:5000/api/inputs
```

#### Example response
```
{
  "id": 3,
  "uid": "input3"
}
```

### Update an input
Update an existing input. The `id` (integer) of the input is required in the path.

- Path: `/api/inputs/<id>`
- Method: `POST`
- Request body: JSON, containing a dictionary with the changes.

#### Command-line curl example
```
# Change the state of input 1 to PAUSED
curl -X POST -d '{"state": "PAUSED"}' http://localhost:5000/api/inputs/1
```

### Delete an input
Delete an input. The `id` (integer) of the input is required in the path.

- Path: `/api/inputs/<id>`
- Method: `DELETE`

#### Command-line curl example
```
# Delete input 1
curl -X DELETE http://localhost:5000/api/inputs/1
```

#### Response (if successful)

```
{"status": "OK"}
```


## Mixers

### Get all mixers
Get an array of all mixers.

- Path: `/api/mixers`
- Method: `GET`

#### Command-line curl example
```
curl http://localhost:5000/api/mixers
```

### Create a mixer
Create a new mixer. Optionally, provide, width, height and pattern. See [Mixers](mixers.md) for more information on these properties.

- Path: `/api/mixers`
- Method: `PUT`
- Request body: JSON, containing a dictionary with the required parameters.

#### Command-line curl example
```
# Create a mixer with default values:
curl -X PUT -d '{}' http://localhost:5000/api/mixers

# Create a mixer, of size 1280x720, with a black background
curl -X PUT -d '{"pattern": 2, "width": 1280, "height": 720}' http://localhost:5000/api/mixers

# Create a mixer, taking input1 as a source
curl -X PUT -d '{"sources": [{"uid": "input1"}]}' http://localhost:5000/api/mixers

```

#### Example response
```
{
  "id": 3,
  "uid": "mixer3"
}
```

### Update a mixer
Update an existing mixer. The `id` (integer) of the mixer is required in the path.

- Path: `/api/mixers/<id>`
- Method: `POST`
- Request body: JSON, containing a dictionary with the changes.

#### Command-line curl example
```
# Change mixer 1 to have a snow background
curl -X POST -d '{"pattern": 1}' http://localhost:5000/api/mixers/1
```

### Cut to a different source
To switch (cut) a mixer to a different source. A source can be an input or another mixer. Any other source(s) currently shown on the mixer will be removed.

- Path: `/api/mixers/<id>/cut_to_source`
- Method: `POST`
- Request body: JSON containing a `source` value with the `uid` of the input/mixer to cut to. For example:

```
{"source": "input1"}
```

#### Command-line curl example
```
# Change mixer 1 to that it's showing input 1
curl -X POST -d '{"source": "input1"}' http://localhost:5000/api/mixers/1/cut_to_source
```

### Overlay source
Like `cut_to_source` above, but overlays a source into a mix without removing any other sources.

- Path: `/api/mixers/<id>/overlay_source`
- Method: `POST`
- Request body: JSON containing a `source` value with the `uid` of the input/mixer to overlay.

#### Command-line curl example
```
# Change mixer 2 to that it's showing input 3
curl -X POST -d '{"source": "input3"}' http://localhost:5000/api/mixers/2/overlay_source
```

### Remove source
Removes a source from a mix.

- Path: `/api/mixers/<id>/remove_source`
- Method: `POST`
- Request body: JSON containing a `source` value with the `uid` of the input/mixer to overlay.

#### Command-line curl example
```
# Remove mixer2 from being a source of mixer 1
curl -X POST -d '{"source": "mixer2"}' http://localhost:5000/api/mixers/1/remove_source
```

### Delete a mixer
Delete a mixer. The `id` (integer) of the mixer is required in the path.

- Path: `/api/mixers/<id>`
- Method: `DELETE`

#### Command-line curl example
```
# Delete mixer 1
curl -X DELETE http://localhost:5000/api/mixers/1
```

#### Response (if successful)

```
{"status": "OK"}
```


## Outputs
There are different types of output, which can be created, updated and deleted. [Read about output types.](outputs.md)

### Get all outputs
Get an array of all outputs.

- Path: `/api/outputs`
- Method: `GET`

#### Command-line curl example
```
curl http://localhost:5000/api/outputs
```

### Create an output
Create a new output. There are different types of outputs. You must specify a `type`, and [depending on the output type chosen](./outputs.md), there may be other required or optional parameters.

- Path: `/api/outputs`
- Method: `PUT`
- Request body: JSON, containing a dictionary with the required parameters.

#### Command-line curl example
```
# Create a file output, that takes the output of mixer1, and writes it to an MP4 file:
curl -X PUT -d '{"type": "file", "source": "mixer1", "location": "/tmp/file.mp4"}' http://localhost:5000/api/outputs
```

#### Example response
```
{
  "id": 3,
  "uid": "output3"
}
```

### Update an output
Update an existing output. The `id` (integer) of the output is required in the path.

- Path: `/api/outputs/<id>`
- Method: `POST`
- Request body: JSON containing the changes

#### Command-line curl example
```
# Change the state of output 1 to READY
curl -X POST -d '{"state": "READY"}' http://localhost:5000/api/outputs/1

# Change the source of output 1 to input 2
curl -X POST -d '{"source": "input2"}' http://localhost:5000/api/outputs/1
```

### Delete an output
Delete an output. The `id` (integer) of the output is required in the path.

- Path: `/api/outputs/<id>`
- Method: `DELETE`

#### Command-line curl example
```
# Delete output 1
curl -X DELETE http://localhost:5000/api/outputs/1
```

#### Response (if successful)

```
{"status": "OK"}
```


## Overlays
Overlays can be applied to inputs and mixers. [Read about overlay types.](overlays.md)

### Get all overlays
Get an array of all overlays.

- Path: `/api/overlays`
- Method: `GET`

#### Command-line curl example
```
curl http://localhost:5000/api/overlays
```

### Create an overlay
Create a new overlay. There are different types of overlays. You must specify a `type`, and [depending on the overlay type chosen](./overlays.md), there may be other required or optional parameters.

- Path: `/api/overlays`
- Method: `PUT`
- Request body: JSON, containing a dictionary with the required parameters.

#### Command-line curl example
```
# Create a text overlay, and overlay it on mixer1
curl -X PUT -d '{"type": "text", "source": "mixer1", "text": "What a nice overlay"}' http://localhost:5000/api/overlays
```

#### Example response
```
{
  "id": 2,
  "uid": "overlay2"
}
```

### Update an overlay
Update an existing overlay. The `id` (integer) of the overlay is required in the path.

- Path: `/api/overlays/<id>`
- Method: `POST`
- Request body: JSON, containing a dictionary with the changes.

#### Command-line curl example
```
# Make an overlay visible
curl -X POST -d '{"visible": true}' http://localhost:5000/api/overlays/1
```

### Delete an overlay
Delete an overlay. The `id` (integer) of the overlay is required in the path.

- Path: `/api/overlays/<id>`
- Method: `DELETE`

#### Command-line curl example
```
# Delete overlay 1
curl -X DELETE http://localhost:5000/api/overlays/1
```

#### Response (if successful)

```
{"status": "OK"}
```


## Websocket
A websocket allows clients to be notified of certain events. It is also required to initiate WebRTC as an input or output.

The websocket can be found at the `/socket` path.

_*WARNING* The websocket is especially likely to change! As such this documentation is currently limited._

Each websocket message has a `msg_type` key describing the content.

| `msg_type` value | Description |
| ---------------- | ----------- |
| `update` | A block (input/output/overlay/mixer) has been updated. |
| `delete` | A block (input/output/overlay/mixer) has been deleted. |
| `webrtc-initialising` | Confirms the user's request to instantiate a WebRTC connection. |
| `volume` | Data about the volume of a block |
