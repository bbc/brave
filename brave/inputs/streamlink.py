from brave.inputs.input import Input
from gi.repository import Gst
import brave.config as config
import streamlink

# should input the stream link or use the built in/installed version of it or sym link it
# so we can call it and use it to get the url we want for a stream

class StreamlinkInput(Input):
    '''
    Handles input via URI.
    This can be anything Playbin accepts, including local files and remote streams.
    '''

    def permitted_props(self):
        return {
            **super().permitted_props(),
            'uri': {
                'type': 'str',
            },
            
            'buffer_duration': {
                'type': 'int',
            },
            'loop': {
                'type': 'bool',
                'default': False
            },
            'position': {
                'type': 'int'
            },
            'volume': {
                'type': 'float',
                'default': 1.0
            },
            'width': {
                'type': 'int'
            },
            'height': {
                'type': 'int'
            }
        }

    def create_elements(self):
        # Playbin or playbin3 does all the hard work.
        # Playbin3 works better for continuous playback.
        # But it does not handle RTMP inputs as well.
        # See http://gstreamer-devel.966125.n4.nabble.com/Behavior-differences-between-
        #   decodebin3-and-decodebin-and-vtdec-hw-not-working-on-OSX-td4680895.html
        # should do a check of the url by passing it through the stream link script
        self.suri = ''
        try:
            streams = streamlink.streams(self.uri)
            self.stream = self.uri
            tstream = streams['best']
            self.suri = tstream.url
        except:
            pass
        
        is_rtmp = self.suri.startswith('rtmp')
        playbin_element = 'playbin' if is_rtmp else 'playbin'
        self.create_pipeline_from_string(playbin_element)
        self.playsink = self.pipeline.get_by_name('playsink')
        self.playbin = self.playsink.parent
        self.playbin.set_property('uri', self.suri)
        self.playbin.connect('about-to-finish', self.__on_about_to_finish)

        if config.enable_video():
            self.create_video_elements()
        else:
            self._create_fake_video()

        if config.enable_audio():
            self.create_audio_elements()
        else:
            self._create_fake_audio()

    def _create_fake_video(self):
        fakesink = Gst.ElementFactory.make('fakesink')
        self.playsink.set_property('video-sink', fakesink)

    def _create_fake_audio(self):
        fakesink = Gst.ElementFactory.make('fakesink')
        self.playsink.set_property('audio-sink', fakesink)

    def create_video_elements(self):
        bin_as_string = ('videoconvert ! videoscale ! capsfilter name=capsfilter ! '
                         'queue ! ' + self.default_video_pipeline_string_end())
        bin = Gst.parse_bin_from_description(bin_as_string, True)

        self.capsfilter = bin.get_by_name('capsfilter')
        self.final_video_tee = bin.get_by_name('final_video_tee')
        self.video_output_queue = bin.get_by_name('video_output_queue')
        self._update_video_filter_caps()
        self.playsink.set_property('video-sink', bin)

    def create_audio_elements(self):
        bin = Gst.parse_bin_from_description(
            f'audiorate ! audioconvert ! audioresample ! {config.default_audio_caps()} ! ' +
            'queue' + self.default_audio_pipeline_string_end(), True)
        self.playsink.set_property('audio-sink', bin)
        self.final_audio_tee = bin.get_by_name('final_audio_tee')

    def on_pipeline_start(self):
        '''
        Called when the stream starts
        '''
        for connection in self.dest_connections():
            connection.unblock_intersrc_if_ready()

        # If the user has asked ot start at a certain timespot, do it now
        # (as the position cannot be set until the pipeline is PAUSED/PLAYING):
        self._handle_position_seek()

    def _handle_position_seek(self):
        '''
        If the user has provided a position to seek to, this method handles it.
        '''
        if hasattr(self, 'position') and self.state in [Gst.State.PLAYING, Gst.State.PAUSED]:
            try:
                new_position = float(self.position)
                if self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, new_position):
                    self.logger.debug('Successfully updated position to %s' % new_position)
                else:
                    self.logger.warning('Unable to set position to %s' % new_position)
            except ValueError:
                self.logger.warning('Invalid position %s provided' % self.position)
            delattr(self, 'position')

    def get_input_cap_props(self):
        '''
        Parses the caps that arrive from the input, and returns them.
        This allows the height/width/framerate/audio_rate to be retrieved.
        '''
        elements = {}
        if hasattr(self, 'intervideosink'):
            elements['video'] = self.intervideosink
        if hasattr(self, 'interaudiosink'):
            elements['audio'] = self.interaudiosink

        props = {}
        for (audioOrVideo, element) in elements.items():
            if not element:
                return
            caps = element.get_static_pad('sink').get_current_caps()
            if not caps:
                return
            size = caps.get_size()
            if size == 0:
                return

            structure = caps.get_structure(0)
            props[audioOrVideo + '_caps_string'] = structure.to_string()
            if structure.has_field('framerate'):
                framerate = structure.get_fraction('framerate')
                props['framerate'] = framerate.value_numerator / framerate.value_denominator
            if structure.has_field('height'):
                props['height'] = structure.get_int('height').value
            if structure.has_field('width'):
                props['width'] = structure.get_int('width').value
            if structure.has_field('channels'):
                props[audioOrVideo + '_channels'] = structure.get_int('channels').value
            if structure.has_field('rate'):
                props[audioOrVideo + '_rate'] = structure.get_int('rate').value

        return props

    def _can_move_to_playing_state(self):
        '''
        Blocks moving into the PLAYING state if buffering is happening
        '''
        buffering_stats = self.get_buffering_stats()
        if not buffering_stats or not buffering_stats.busy:
            return True
        self.logger.debug('Buffering, so not moving to PLAYING')
        return False

    def get_buffering_stats(self):
        '''
        Returns an object with 'busy' (whether buffering is in progress)
        and 'percent' (the amount of buffering retrieved, 100=full buffer)
        '''
        query_buffer = Gst.Query.new_buffering(Gst.Format.PERCENT)
        result = self.pipeline.query(query_buffer)
        return query_buffer.parse_buffering_percent() if result else None

    def summarise(self, for_config_file=False):
        '''
        Adds buffering stats to the summary
        '''
        s = super().summarise(for_config_file)
        if not for_config_file:
            buffering_stats = self.get_buffering_stats()
            if buffering_stats:
                s['buffering_percent'] = buffering_stats.percent
        return s

    def on_buffering(self, buffering_percent):
        '''
        Called to report buffering.
        '''
        # If buffering is 100% it might be time to go to the PLAYING state:
        if buffering_percent == 100:
            self._consider_changing_state()
        else:
            self.report_update_to_user()

    def handle_updated_props(self):
        super().handle_updated_props()
        self._handle_position_seek()
        if hasattr(self, 'buffer_duration'):
            self.playbin.set_property('buffer-duration', self.buffer_duration)
        if hasattr(self, 'volume'):
            self.playbin.set_property('volume', self.volume)

    def __on_about_to_finish(self, playbin):
        if self.loop:
            self.logger.debug('About to finish, looping')
            playbin.set_property('uri', self.suri)
