from brave.outputs.local import LocalOutput
from brave.outputs.rtmp import RTMPOutput
from brave.outputs.tcp import TCPOutput
from brave.outputs.image import ImageOutput
from brave.outputs.file import FileOutput
from brave.outputs.webrtc import WebRTCOutput
from brave.abstract_collection import AbstractCollection


class OutputCollection(AbstractCollection):
    def add(self, **args):
        args['id'] = self.get_new_id()

        if args['type'] == 'local':
            output = LocalOutput(**args, collection=self)
        elif args['type'] == 'rtmp':
            output = RTMPOutput(**args, collection=self)
        elif args['type'] == 'tcp':
            output = TCPOutput(**args, collection=self)
        elif args['type'] == 'image':
            output = ImageOutput(**args, collection=self)
        elif args['type'] == 'file':
            output = FileOutput(**args, collection=self)
        elif args['type'] == 'webrtc':
            output = WebRTCOutput(**args, collection=self)
        else:
            raise Exception(f"Invalid output type '{str(args['type'])}'")

        self._items[args['id']] = output
        return output
