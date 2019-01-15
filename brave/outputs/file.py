from brave.outputs.output import Output
import brave.config as config
from gi.repository import Gst


class FileOutput(Output):
    '''
    For outputing to a file
    '''

    def permitted_props(self):
        return {
            **super().permitted_props(),
            'width': {
                'type': 'int',
                'default': config.default_mixer_width()
            },
            'height': {
                'type': 'int',
                'default': config.default_mixer_height()
            },
            'location': {
                'type': 'str'
            }
        }

    def create_elements(self):
        pipeline_string = 'mp4mux name=mux ! filesink name=sink'

        if config.enable_video():
            pipeline_string += ' ' + self._video_pipeline_start() + 'x264enc name=video_encoder ! queue ! mux.'

        if config.enable_audio():
            audio_pipeline_string = ('interaudiosrc name=interaudiosrc ! '
                                     'audioconvert ! audioresample ! avenc_aac name=audio_encoder')

            # A larger queue size enables the video encoder to take longer
            audio_pipeline_string += f' ! queue max-size-bytes={10*(3 ** 20)} ! mux.'

            pipeline_string = pipeline_string + ' ' + audio_pipeline_string

        self.create_pipeline_from_string(pipeline_string)
        self.logger.debug('Writing to the file ' + self.location)
        sink = self.pipeline.get_by_name('sink')
        sink.set_property('location', self.location)

        if config.enable_video():
            self.video_encoder = self.pipeline.get_by_name('video_encoder')

        if config.enable_audio():
            self.audio_encoder = self.pipeline.get_by_name('audio_encoder')

    def set_state(self, new_state):
        sent_eos = False
        # If this is ending the file creation (identified by moving to READY or NULL)
        # we must send an EOS so that the file is completed correctly.
        if (new_state == Gst.State.READY or new_state == Gst.State.NULL):

            for encoder_name in ['video_encoder', 'audio_encoder']:
                if hasattr(self, encoder_name):
                    encoder = getattr(self, encoder_name)
                    encoder_state = encoder.get_state(0).state
                    if encoder_state in [Gst.State.PAUSED, Gst.State.PLAYING]:
                        if encoder.send_event(Gst.Event.new_eos()):
                            self.logger.debug('Successfully send EOS event to the ' + encoder_name)
                            sent_eos = True
                        else:
                            self.logger.warning('Failed to send EOS event to the %s' % encoder_name)

        # If we've sent an EOS, allow that to propogate the pipeline.
        # (Separate code will then catch the EOS successful message and cause a state change.)
        # Otherwise, lets go ahead and set the state of the pipeline.
        if sent_eos:
            return True

        return super().set_state(new_state)

    def create_caps_string(self):
        # format=I420 ensures the mp4 is playable with QuickTime.
        return super().create_caps_string(format='I420')
