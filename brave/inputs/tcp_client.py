from brave.inputs.input import Input
from gi.repository import Gst
import brave.config as config
import brave.exceptions


class TcpClientInput(Input):
    '''
    Allows an an input by receiving from another server via TCP.
    Basically using the `tcpclientsrc` element.
    '''

    def permitted_props(self):
        return {
            **super().permitted_props(),
            'host': {
                'type': 'str',
                'required': True
            },
            'port': {
                'type': 'int',
                'required': True
            },
            'volume': {
                'type': 'float',
                'default': 0.8
            },
            'width': {
                'type': 'int'
            },
            'height': {
                'type': 'int'
            },
            'xpos': {
                'type': 'int',
                'default': 0
            },
            'ypos': {
                'type': 'int',
                'default': 0
            },
            'zorder': {
                'type': 'int',
                'default': 1
            },
            'container': {
                'type': 'str',
                'default': 'mpeg',
                'permitted_values': {
                    'mpeg': 'MPEG',
                    'ogg': 'OGG'
                }
            }
        }

    def create_elements(self):
        '''
        Creates the pipeline with elements needed to accept a TCP connection.
        '''

        # We support ogg and mpeg containers; the right demuxer must be used:
        demux_element = 'oggdemux' if self.container == 'ogg' else 'tsdemux'

        # We start with tcpclientsrc, and immediately demux it into audio and video.
        pipeline_string = 'tcpclientsrc name=tcpclientsrc ! %s name=demux ' % demux_element

        if self.has_video():
            # We need to decode the video:
            pipeline_string += (' queue2 max-size-time=3000000000 name=demux_to_video_queue ! '
                                'decodebin name=video_decodebin ')
            # This then can be connected to the common bit of the pipeline:
            pipeline_string += self.default_video_pipeline_string_end()
        else:
            # If we don't want the video, dump it:
            pipeline_string += 'fakesink'

        if self.has_audio():
            # The audio part also needs a decodebin:
            pipeline_string += (' queue2 max-size-time=3000000000 name=demux_to_audio_queue'
                                ' ! decodebin name=audio_decodebin')

            # We will then connect this decodebin to aan audio convert/resample
            pipeline_string += ' audioconvert name=audioconvert ! audioresample ! ' + \
                config.default_audio_caps() + \
                self.default_audio_pipeline_string_end()

        self.create_pipeline_from_string(pipeline_string)
        tcpclientsrc = self.pipeline.get_by_name('tcpclientsrc')
        tcpclientsrc.set_property('host', self.host)
        tcpclientsrc.set_property('port', self.port)

        if self.has_video():
            self.final_video_tee = self.pipeline.get_by_name('final_video_tee')
            self.demux_to_video_queue = self.pipeline.get_by_name('demux_to_video_queue')
            self.video_element_after_demux = self.pipeline.get_by_name('video_output_queue')
            video_decodebin = self.pipeline.get_by_name('video_decodebin')
            video_decodebin.connect('pad-added', self._on_decodebin_pad_added)

        if self.has_audio():
            self.final_audio_tee = self.pipeline.get_by_name('final_audio_tee')
            self.demux_to_audio_queue = self.pipeline.get_by_name('demux_to_audio_queue')
            self.audio_element_after_demux = self.pipeline.get_by_name('audioconvert')
            audio_decodebin = self.pipeline.get_by_name('audio_decodebin')
            audio_decodebin.connect('pad-added', self._on_decodebin_pad_added)

        demux = self.pipeline.get_by_name('demux')
        demux.connect('pad-added', self._on_demux_pad_added)

    def _on_demux_pad_added(self, _, pad):
        '''
        Demux creates new pads every time the stream starts.
        This handles the creation of a new pad by linking it to the relevant element.
        The pipeline is:
        - For video: demuxer --> demux_to_video_queue --> decodebin --> ...
        - For audio: demuxer --> demux_to_audio_queue --> decodebin --> ...
        '''
        if not pad.has_current_caps():
            return

        caps = pad.get_current_caps()
        structure = caps.get_structure(0)
        name = structure.get_name()
        element_to_connect_to = None
        if name.startswith('video'):
            if hasattr(self, 'demux_to_video_queue'):
                element_to_connect_to = self.demux_to_video_queue

        elif name.startswith('audio'):
            if hasattr(self, 'demux_to_audio_queue'):
                element_to_connect_to = self.demux_to_audio_queue

        else:
            raise brave.exceptions.PipelineFailure('TCP Client: Unexpected pad name %s' % name)

        if not element_to_connect_to:
            return

        pad_to_connect_to = element_to_connect_to.get_static_pad('sink')
        if pad.link(pad_to_connect_to) is not Gst.PadLinkReturn.OK:
            self.logger.warning('Unable to connect demuxer to queue')

    def _on_decodebin_pad_added(self, _, pad):
        '''
        Like demux, decodebin creates new pads every time the stream starts.
        This handles the creation of a new pad by linking it to the relevant element.
        The pipeline is:
        - For video: decodebin --> video_output_queue --> tee --> ...
        - For audio: decodebin --> audioconvert --> audioresample --> ...
        '''
        if not pad.has_current_caps():
            return

        caps = pad.get_current_caps()
        structure = caps.get_structure(0)
        name = structure.get_name()
        element_to_connect_to = None
        if name.startswith('video'):
            element_to_connect_to = self.video_element_after_demux
        elif name.startswith('audio'):
            element_to_connect_to = self.audio_element_after_demux
        else:
            raise brave.exceptions.PipelineFailure('TCP Client: Unexpected decodebin pad name %s' % name)

        pad_to_connect_to = element_to_connect_to.get_static_pad('sink')
        if pad.link(pad_to_connect_to) is not Gst.PadLinkReturn.OK:
            self.logger.warning('Unable to connect demuxer to queue')
