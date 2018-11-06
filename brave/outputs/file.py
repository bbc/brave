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
        self._create_initial_multiqueue()
        pipeline_string = 'mp4mux name=mux ! filesink name=sink'

        if config.enable_video():
            video_pipeline_string = ('intervideosrc name=intervideosrc ! videoconvert ! '
                                     'videoscale ! videorate ! '
                                     f'{self.create_caps_string()} ! '
                                     'x264enc name=video_encoder ! queue ! mux.')

            pipeline_string = pipeline_string + ' ' + video_pipeline_string

        if config.enable_audio():
            audio_pipeline_string = ('interaudiosrc name=interaudiosrc ! '
                                     'audioconvert ! audioresample ! faac name=audio_encoder')

            # A larger queue size enables the video encoder to take longer
            audio_pipeline_string += f' ! queue max-size-bytes={10*(3 ** 20)} ! mux.'

            pipeline_string = pipeline_string + ' ' + audio_pipeline_string

        if not self.create_pipeline_from_string(pipeline_string):
            return

        self.logger.debug('Writing to the file ' + self.props['location'])
        sink = self.pipeline.get_by_name('sink')
        sink.set_property('location', self.props['location'])

        if config.enable_video():
            self.video_encoder = self.pipeline.get_by_name('video_encoder')
            self.intervideosrc = self.pipeline.get_by_name('intervideosrc')
            self.intervideosrc_src_pad = self.intervideosrc.get_static_pad('src')
            self.create_intervideosink_and_connections()

        if config.enable_audio():
            self.audio_encoder = self.pipeline.get_by_name('audio_encoder')
            self.interaudiosrc = self.pipeline.get_by_name('interaudiosrc')
            self.interaudiosrc_src_pad = self.interaudiosrc.get_static_pad('src')
            self.create_interaudiosink_and_connections()

        self._sync_elements_on_source_pipeline()

    def set_state(self, new_state):
        sent_eos = False
        # If this is ending the file creation (identified by moving to READY or NULL)
        # we must send an EOS so that the file is completed correctly.
        if (new_state == Gst.State.READY or new_state == Gst.State.NULL):

            for encoder_name in ['video_encoder', 'audio_encoder']:
                if hasattr(self, encoder_name):
                    encoder = getattr(self, encoder_name)
                    encoder_state = encoder.get_state(0).state
                    if encoder_state == Gst.State.PAUSED or encoder_state == Gst.State.PLAYING:
                        if encoder.send_event(Gst.Event.new_eos()):
                            self.logger.debug('Successfully send EOS event to the ' + encoder_name)
                            sent_eos = True
                        else:
                            self.logger.warn('Failed to send EOS event')

        # If we've sent an EOS, allow that to propogate the pipeline.
        # (Separate code will then catch the EOS successful message and cause a state change.)
        # Otherwise, lets go ahead and set the state of the pipeline.
        if sent_eos:
            return True

        return super().set_state(new_state)

    # def create_caps_string(self):
    #     return super().create_caps_string() + ',format=YUV'
