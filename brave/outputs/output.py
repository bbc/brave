from gi.repository import Gst
from brave.helpers import round_down
import brave.exceptions
from brave.inputoutputoverlay import InputOutputOverlay


class Output(InputOutputOverlay):
    '''
    An abstract superclass representing an output.
    '''

    def __init__(self, **args):
        if 'name' in args:
            self.name = args["name"]
            del args["name"]
        if 'source' in args:
            source_uid = args['source']
            del args['source']
        else:
            source_uid = 'default'

        super().__init__(**args)
        self.create_elements()

        if self.has_video():
            self.pipeline.get_by_name('capsfilter')\
                .set_property('caps', Gst.Caps.from_string(self.create_caps_string()))
            self.intervideosrc = self.pipeline.get_by_name('intervideosrc')
            self.intervideosrc_src_pad = self.intervideosrc.get_static_pad('src')

        if self.has_audio():
            self.interaudiosrc = self.pipeline.get_by_name('interaudiosrc')
            self.interaudiosrc_src_pad = self.interaudiosrc.get_static_pad('src')

        self._set_source(source_uid)
        self.setup_complete = True
        self._consider_changing_state()

    def input_output_overlay_or_mixer(self):
        return 'output'

    def summarise(self, for_config_file=False):
        s = super().summarise(for_config_file)
        s['source'] = self.source().uid if self.source() else None
        return s

    def source(self):
        '''
        Returns the Input or Mixer object that is the source for this output.
        Can be None if this output thas no source.
        '''
        connection = self.source_connection()
        return connection.source if connection else None

    def source_connection(self):
        '''
        Returns an the Connection object which describes what this output is connected to.
        If this output is not connected to anything, returns None.
        An output can be the destination to exactly one connection.
        The source of a connection will be either an Input or a Mixer.
        '''
        return self.session().connections.get_first_for_dest(self)

    def source_connections(self):
        '''
        As source_connection() but returns an array of the 1 connected source, or an empty array if no attached source.
        '''
        return self.session().connections.get_all_for_source(self)

    def connection_for_source(self, input_or_mixer, create_if_not_made=False):
        '''
        Given an input or mixer, gets the Connection from it to this.
        If such a Connection has not been made before, makes it.
        '''
        if create_if_not_made:
            return self.session().connections.get_or_add_connection_between_source_and_dest(input_or_mixer, self)
        else:
            return self.session().connections.get_connection_between_source_and_dest(input_or_mixer, self)

    def update(self, updates):
        '''
        Overridden update() method to handle an update the source of this output.
        '''
        if 'source' in updates and (not self.source() or updates['source'] != self.source().uid):
            if self.state in [Gst.State.PLAYING, Gst.State.PAUSED]:
                raise brave.exceptions.InvalidConfiguration(
                    'Cannot change an output\'s source whilst it is in PAUSED or PLAYING state')
            self._set_source(updates['source'])
            del updates['source']
        super().update(updates)

    def delete(self):
        self.logger.info('Being deleted')
        if self.source_connection():
            self.source_connection().delete()
        super().delete()

    def create_caps_string(self, format='RGBx'):
        '''
        Returns the preferred caps (a string defining things such as width, height and framerate)
        '''

        caps = 'video/x-raw,format=%s,pixel-aspect-ratio=1/1' % format

        # If only one dimension is provided, we calculate the other.
        # Some encoders (jpegenc, possibly others) don't like it if only one metric is present.
        width = self.width if hasattr(self, 'width') else 0
        height = self.height if hasattr(self, 'height') else 0
        if self.source():
            src_width, src_height = self.source().get_dimensions()
            if src_width and src_height:
                if width and not height:
                    height = round_down(width * src_height / src_width)
                if height and not width:
                    width = round_down(height * src_width / src_height)
                if not width and not height:
                    width, height = src_width, src_height

        # Some encoders don't like odd-numbered widths:
        if width and width % 2 == 1:
            width += 1

        if width and height:
            caps += ',width=%s,height=%s' % (width, height)

        self.logger.debug('Caps created:' + caps)
        return caps

    def on_pipeline_start(self):
        '''
        Called when the stream starts
        '''
        if self.source_connection():
            self.source_connection().unblock_intersrc_if_ready()

    def _set_source(self, new_src_uid):
        '''
        Ensure the source of this output (either an input or mixer) is correctly set up.
        '''
        if new_src_uid is None:
            if self.source_connection():
                self.source_connection().delete()
            return
        elif new_src_uid == 'default':
            new_src = self.session().mixers.get_entry_with_lowest_id()
            if not new_src:
                return
        else:
            new_src = self.session().uid_to_block(new_src_uid, error_if_not_exists=True)

        if self.source() == new_src:
            return

        if self.source():
            self.logger.info('Request to change source from %s to %s' % (self.source().uid, new_src.uid))
            self.source_connection().delete()

        self.session().connections.get_or_add_connection_between_source_and_dest(new_src, self)
        self.source_connection().setup()

    def _video_pipeline_start(self):
        '''
        The standard start to the pipeline string for video.
        It starts with intervideosrc, which accepts video from the source.
        '''
        # The large timeout holds any stuck frame for 24 hours (basically, a very long time)
        # This is optional, but prevents it from going black when it's better to show the last frame.
        timeout = Gst.SECOND * 60 * 60 * 24
        return ('intervideosrc name=intervideosrc timeout=%d ! videoconvert ! videoscale ! '
                'videorate ! capsfilter name=capsfilter ! ' % timeout)

    def _audio_pipeline_start(self):
        '''
        The standard start to the pipeline string for audio.
        It starts with interaudiosrc, which accepts audio from the source.
        '''
        return 'interaudiosrc name=interaudiosrc ! audioconvert ! audioresample ! '
