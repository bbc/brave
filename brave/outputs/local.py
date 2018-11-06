from brave.outputs.output import Output
import brave.config as config
import brave.exceptions


class LocalOutput(Output):
    '''
    For previewing audio and video locally.
    '''

    def permitted_props(self):
        return {
            **super().permitted_props(),
            'width': {
                'type': 'int',
                'default': 640,
            },
            'height': {
                'type': 'int',
                'default': 360
            }
        }

    def check_item_can_be_created(self):
        '''
        Prevent more than one local output from being created. It crashes (on MacOS at least).
        '''
        other_local_outputs = dict((k, v) for k, v in self.session().outputs.items() if isinstance(v, LocalOutput))
        if len(other_local_outputs):
            raise brave.exceptions.InvalidConfiguration('There cannot be more than one local output')

    def create_elements(self):
        self._create_initial_multiqueue()

        pipeline_string = ''
        if config.enable_video():
            # format=RGB removes the alpha channel which can crash autovideosink
            video_caps = 'video/x-raw,format=RGB,width=%d,height=%d,pixel-aspect-ratio=1/1' % \
                (self.props['width'], self.props['height'])

            pipeline_string += ('intervideosrc name=intervideosrc ! videoconvert ! videoscale ! ' +
                                video_caps + ' ! queue ! autovideosink')
        if config.enable_audio():
            pipeline_string += ' interaudiosrc name=interaudiosrc ! queue ! autoaudiosink'

        if not self.create_pipeline_from_string(pipeline_string):
            return False

        if config.enable_video():
            self.intervideosrc = self.pipeline.get_by_name('intervideosrc')
            self.intervideosrc_src_pad = self.intervideosrc.get_static_pad('src')
            self.create_intervideosink_and_connections()

        if config.enable_audio():
            self.interaudiosrc = self.pipeline.get_by_name('interaudiosrc')
            self.interaudiosrc_src_pad = self.interaudiosrc.get_static_pad('src')
            self.create_interaudiosink_and_connections()
