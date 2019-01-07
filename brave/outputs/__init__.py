from brave.outputs.local import LocalOutput
from brave.outputs.rtmp import RTMPOutput
from brave.outputs.tcp import TCPOutput
from brave.outputs.image import ImageOutput
from brave.outputs.file import FileOutput
from brave.outputs.webrtc import WebRTCOutput
from brave.outputs.kvs import KvsOutput
from brave.abstract_collection import AbstractCollection
import brave.exceptions


class OutputCollection(AbstractCollection):
    def add(self, **args):
        args['id'] = self.get_new_id()

        if 'type' not in args:
            raise brave.exceptions.InvalidConfiguration("Invalid output, no 'type'")
        elif args['type'] == 'local':
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
        elif args['type'] == 'kvs':
            output = KvsOutput(**args, collection=self)
        else:
            raise brave.exceptions.InvalidConfiguration("Invalid output type '%s'" % args['type'])

        self._items[args['id']] = output
        return output
