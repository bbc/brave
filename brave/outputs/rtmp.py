from brave.outputs.output import Output
from gi.repository import Gst
import brave.config as config


class RTMPOutput(Output):
    '''
    For sending an output to a third-party RTMP server (such as Facebook Live).
    '''

    def permitted_props(self):
        return {
            'uri': {
                'type': 'str'
            },
            'width': {
                'type': 'int',
                'default': config.default_mixer_width()
            },
            'height': {
                'type': 'int',
                'default': config.default_mixer_height()
            }
        }

    def create_elements(self):
        '''
        Create the elements needed whether this is audio, video, or both
        '''

        self._create_initial_multiqueue()
        pipeline_string = 'flvmux name=mux streamable=true ! rtmpsink name=sink'

        if config.enable_video():
            # framerate=30/1 because Facebook Live and YouTube live want this framerate.
            # profile=baseline may be superflous but some have recommended it for Facebook
            video_caps = 'video/x-h264,framerate=30/1,profile=baseline,width=%d,height=%d,format=YUV' % \
                (self.props['width'], self.props['height'])

            # key-int-max=60 puts a keyframe every 2 seconds (60 as 2*framerate)
            pipeline_string = (pipeline_string +
                               ' intervideosrc name=intervideosrc ! videorate ! videoconvert ! videoscale ! ' +
                               ' x264enc name=video_encoder key-int-max=60 ! ' + video_caps +
                               ' ! h264parse ! queue ! mux.')
        if config.enable_audio():
            pipeline_string = pipeline_string + \
                ' interaudiosrc name=interaudiosrc ! faac name=audio_encoder ! ' + \
                'aacparse ! audio/mpeg, mpegversion=4 ! queue ! mux.'

        self.logger.debug('Creating RTMP output with this pipeline: ' + pipeline_string)
        if not self.create_pipeline_from_string(pipeline_string):
            return False
        self.pipeline.get_by_name('sink').set_property('location', self.props['uri'] + ' live=1')

        if config.enable_video():
            self.intervideosrc = self.pipeline.get_by_name('intervideosrc')
            self.intervideosrc_src_pad = self.intervideosrc.get_static_pad('src')
            self.create_intervideosink_and_connections()

        if config.enable_audio():
            self.interaudiosrc = self.pipeline.get_by_name('interaudiosrc')
            self.interaudiosrc_src_pad = self.interaudiosrc.get_static_pad('src')
            self.create_interaudiosink_and_connections()

        # We set to PAUSED rather than PLAYING because the audio encode needs a moment in preroll.
        # Without this, a not-negotiated error will occur.
        # For now, we leave it up to the user to put it into the PLAYING state.
        # A better solution would be to listen out for the successful prep of the pipeline
        # and then move into PLAYING.
        change_to_paused_state_response = self.pipeline.set_state(Gst.State.PAUSED)
        if change_to_paused_state_response == Gst.StateChangeReturn.NO_PREROLL:
            self.logger.debug('Moved to PAUSED state but preroll preparation still underway')
        elif change_to_paused_state_response != Gst.StateChangeReturn.SUCCESS:
            self.logger.warn('Unable to change into PAUSED state:' + str(change_to_paused_state_response))

        self._sync_elements_on_source_pipeline()

        self.logger.info('RTMP output now configured to send to ' + self.props['uri'])
