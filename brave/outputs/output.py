from gi.repository import Gst
from brave.helpers import round_down
import brave.exceptions
from brave.inputoutputoverlay import InputOutputOverlay


class Output(InputOutputOverlay):
    '''
    An abstract superclass representing an output.
    '''

    def __init__(self, **args):
        source_uid = None
        if 'source' in args:
            source_uid = args['source']
            del args['source']

        super().__init__(**args)
        self.intersrc_src_pad_probe = {}

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

        # Set initially to READY, and when there we set to self.props['initial_state']
        self.set_state(Gst.State.READY)

    def input_output_overlay_or_mixer(self):
        return 'output'

    def summarise(self):
        s = super().summarise()
        if self.src():
            s['source'] = self.src().uid()
        return s

    def src(self):
        '''
        Returns the Input or Mixer that is the source for this output.
        Can be None if this outpu thas no source.
        '''
        connection = self.src_connection()
        return connection.src if connection else None

    def src_connection(self):
        '''
        Returns an the Connection object which describes what this output is connected to.
        If this output is not connected to anything, returns None.
        An output can be the destination to exactly one connection.
        The source of a connection will be either an Input or a Mixer.
        '''
        return self.session().connections.get_first_collection_for_dest(self)

    def src_connections(self):
        '''
        As src_connection() but returns an array of the 1 connected source, or an empty array if no attached source.
        '''
        return self.session().connections.get_all_collections_for_src(self)

    def connection_for_src(self, input_or_mixer, create_if_not_made=False):
        '''
        Given an input or mixer, gets the Connection from it to this.
        If such a Connection has not been made before, makes it.
        '''
        if create_if_not_made:
            return self.session().connections.get_or_add_connection_between_src_and_dest(input_or_mixer, self)
        else:
            return self.session().connections.get_connection_between_src_and_dest(input_or_mixer, self)

    def update(self, updates):
        '''
        Overridden update() method to handle an update the source of this output.
        '''
        if 'source' in updates and (not self.src() or updates['source'] != self.src().uid):
            if self.get_state() in [Gst.State.PLAYING, Gst.State.PAUSED]:
                raise brave.exceptions.InvalidConfiguration(
                    'Cannot change an output\'s source whilst it is in PAUSED or PLAYING state')
            self._set_source(updates['source'])
        super().update(updates)

    def delete(self):
        self.logger.info('Being deleted')
        if self.src_connection():
            self.src_connection().delete()
        super().delete()

    def create_caps_string(self):
        '''
        Returns the preferred caps (a string defining things such as width, height and framerate)
        '''

        # Don't set 'format' here... output types set their own.
        caps = 'video/x-raw'

        # If only one dimension is provided, we calculate the other.
        # Some encoders (jpegenc, possibly others) don't like it if only one metric is present.
        width = self.props['width'] if 'width' in self.props else None
        height = self.props['height'] if 'height' in self.props else None
        if self.src():
            src_width, src_height = self.src().get_dimensions()
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
        if self.src_connection():
            self.src_connection().unblock_intersrc_if_ready()

    def _set_source(self, new_src_uid):
        '''
        Ensure the source of this output (either an input or mixer) is correctly set up.
        '''
        new_src = None
        if new_src_uid:
            if new_src_uid == 'none':
                if self.src_connection():
                    self.src_connection().delete()
                return
            else:
                new_src = self.session().uid_to_block(new_src_uid)
                if new_src is None:
                    raise brave.exceptions.InvalidConfiguration('Unknown source "%s"' % new_src_uid)

        else:
            # Default is to mixer0 if it exists; otherwise, do nothing
            if 0 in self.session().mixers:
                new_src = self.session().mixers[0]
            else:
                return

        if self.src() == new_src:
            return

        if self.src():
            self.logger.info('Request to change source from %s to %s' % (self.src().uid(), new_src.uid()))
            self.src_connection().delete()

        self.session().connections.get_or_add_connection_between_src_and_dest(new_src, self)
        self.src_connection().setup()

    def _video_pipeline_start(self):
        '''
        The standard start to the pipeline string for video.
        It starts with intervideosrc, which accepts video from the source.
        '''
        return ('intervideosrc name=intervideosrc ! videoconvert ! videoscale ! '
                'videorate ! capsfilter name=capsfilter ! ')

    def _audio_pipeline_start(self):
        '''
        The standard start to the pipeline string for audio.
        It starts with interaudiosrc, which accepts audio from the source.
        '''
        return 'interaudiosrc name=interaudiosrc ! audioconvert ! audioresample ! '
