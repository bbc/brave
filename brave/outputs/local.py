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
        pipeline_string = ''
        if config.enable_video():
            pipeline_string += self._video_pipeline_start() + 'queue ! glimagesink'
        if config.enable_audio():
            pipeline_string += ' interaudiosrc name=interaudiosrc ! queue ! autoaudiosink'

        self.create_pipeline_from_string(pipeline_string)

    def create_caps_string(self):
        # format=RGB removes the alpha channel which can crash glimagesink
        return super().create_caps_string() + ',pixel-aspect-ratio=1/1,format=RGB'
