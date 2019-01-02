# Brave API

Brave has a RESTful JSON API that allows you to dynamically add and remove inputs, mixers, outputs and overlays. It is designed to be fast, simple, and stateless.

(You can also configure Brave at startup using the [YAML config file](config_file.md)).

A [websocket connection](#websocket) is also available for when your client wishes to be notified of updates (e.g. when an input ends).

## Contents
- [General](#general-api-calls)
- [Inputs](#Inputs)
- [Outputs](#Outputs)
- [Mixers](#mixers)
- [Overlays](#overlays)
- [Websocket](#websocket)

## General API calls

### `GET /api/all` - Get details on all inputs/outputs/mixers/overlays
Retrieves information on all created items (blocks). The response is a map (dictonary) with four keys for the four types (`inputs`, `outputs`, `mixers`, and `overlays`). If you only need one of these types, use the relevant call for that, e.g.  [`/api/inputs`](#get-all-inputs).

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
   "inputs":[  
      {  
         "has_audio":false,
         "has_video":true,
         "uid":"input2",
         "state":"PLAYING",
         "id":2,
         "type":"test_video",
         "props":{  
            "initial_state":"PLAYING",
            "pattern":0,
            "width":640,
            "height":360,
            "xpos":0,
            "ypos":0,
            "zorder":5
         },
         "position":5744090119
      }
   ],
   "overlays":[  

   ],
   "outputs":[  
      {  
         "has_audio":true,
         "has_video":true,
         "uid":"output1",
         "state":"PLAYING",
         "id":1,
         "type":"tcp",
         "props":{  
            "initial_state":"PLAYING",
            "audio_bitrate":128000,
            "container":"mpeg",
            "host":"127.0.0.1",
            "port":7000
         },
         "source":"mixer1"
      }
   ],
   "mixers":[  
      {  
         "has_audio":true,
         "has_video":true,
         "uid":"mixer1",
         "state":"PLAYING",
         "id":1,
         "type":"mixer",
         "props":{  
            "initial_state":"PLAYING",
            "width":640,
            "height":360,
            "pattern":0
         },
         "sources":[  
            {  
               "uid":"input2",
               "id":2,
               "block_type":"input",
               "in_mix":false
            }
         ]
      }
   ]
}
```

## Inputs
Inputs allow you to source content (e.g. from an RTMP stream or a file.) There can be any number of inputs, and they can be created, updated, and deleted. [Read more about input types.](./inputs.md)


### Get all inputs
Get an array of all inputs.

- Path: `/api/inputs`
- Method: GET


### Create an input
Create a new input. There are different types of inputs. You must specify a `type`, and [depending on the type chosen](./inputs.md), there may be other required or optional parameters.

- Path: `/api/inputs`
- Method: `PUT`

#### Comand-line curl example
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

## Outputs

### Get all outputs
- Path: `/api/outputs`
- Method: GET


## Mixers

TODO

## Overlays

TODO

* The `/all` endpoint describes all inputs, outputs, mixers, and overlays.
* Create a new input with a `PUT` to `/inputs`
* Create a new overlay with a `PUT` to `/overlays`
* Create a new output with a `PUT` to `/outputs`
* Update an existing input or overlay with a `POST`
* Update an existing input, overlay or output with a `DELETE`

curl -X PUT -d '{"pattern": 2}' http://localhost:5000/api/mixers

## Websocket

TODO
