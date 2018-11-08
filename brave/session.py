import os
import sys
import logging
logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO').upper())
logger = logging.getLogger('brave.session')
from gi.repository import Gst, GObject
from brave.inputs import InputCollection
from brave.outputs import OutputCollection
from brave.overlays import OverlayCollection
from brave.mixers import MixerCollection
import brave.config as config
assert Gst.VERSION_MINOR > 13, f'GStreamer is version 1.{Gst.VERSION_MINOR}, must be 1.14 or higher'
PERIODIC_MESSAGE_FREQUENCY = 5 # TEMP
singleton = None


class Session(object):
    '''
    Class to provide the 'session' which allows live AV manipulation.
    '''

    def __init__(self):
        self.logger = logging.getLogger('brave.session')
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s:\033[32m[session]\033[0m %(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False
        self.items_recently_updated = []
        self.items_recently_deleted = []

        self.inputs = InputCollection(self)
        self.outputs = OutputCollection(self)
        self.overlays = OverlayCollection(self)
        self.mixers = MixerCollection(self)

    def start(self):
        self._setup_initial_inputs_outputs_mixers_and_overlays()
        self.mainloop = GObject.MainLoop()
        GObject.timeout_add(PERIODIC_MESSAGE_FREQUENCY * 1000, self.periodic_message)
        self.mainloop.run()
        self.logger.debug('Mainloop has ended')

    def end(self, restart=False):
        '''
        Called when the user has requested the service to end.
        '''
        for name, input in self.inputs.items():
            input.set_state(Gst.State.NULL)
        for name, output in self.outputs.items():
            output.set_state(Gst.State.NULL)
        for name, mixer in self.mixers.items():
            mixer.set_state(Gst.State.NULL)
        self.mainloop.quit()
        if restart:
            os.execl(sys.executable, sys.executable, *sys.argv)

    def _setup_initial_inputs_outputs_mixers_and_overlays(self):
        '''
        Create the inputs/outputs/mixers/overlays declared in the config file.
        '''
        for mixer_config in config.default_mixers():
            self.mixers.add(**mixer_config)

        for output_config in config.default_outputs():
            output = self.outputs.add(**output_config)

        for name, output in self.outputs.items():
            output.link_from_source()

        if config.enable_video():
            for overlay_config in config.default_overlays():
                self.overlays.add(**overlay_config)

        for name, mixer in self.mixers.items():
            mixer.set_state(Gst.State.PLAYING)

        for input_config in config.default_inputs():
            input = self.inputs.add(**input_config)
            for name, mixer in self.mixers.items():
                source = mixer.sources.get_or_create(input)
                source.add_to_mix()

    def print_state_summary(self):
        '''
        Prints the state of all elements to STDOUT.
        '''
        self.inputs.print_state_summary()
        self.outputs.print_state_summary()
        self.overlays.print_state_summary()
        self.mixers.print_state_summary()

    def periodic_message(self):
        self.print_state_summary()
        self.logger.debug('...state will print out every %d seconds...' % PERIODIC_MESSAGE_FREQUENCY)
        GObject.timeout_add(PERIODIC_MESSAGE_FREQUENCY * 1000, self.periodic_message)


def init():
    Gst.init(None)
    global singleton
    singleton = Session()
    return singleton


def get_session():
    global singleton
    return singleton
