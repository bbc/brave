'''
Standard handling of the 'bus' that each pipeline has.
'''
from gi.repository import Gst


def setup_messaging(pipe, parent_object):
    logger = parent_object.logger

    # Some docs on parsing the message can be found at
    # http://lazka.github.io/pgi-docs/#Gst-1.0/flags.html#Gst.MessageType and
    # http://lazka.github.io/pgi-docs/#Gst-1.0/classes/Message.html#Gst.Message.parse_error
    def _on_message(bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            logger.info('Received EOS (End Of Stream)')
            # For file outputs especially, it's important changes the state.
            pipe.set_state(Gst.State.READY)
        elif t == Gst.MessageType.STATE_CHANGED:
            is_pipeline_state_change = isinstance(message.src, Gst.Pipeline)
            if is_pipeline_state_change:
                old_state, new_state, pending_state = message.parse_state_changed()
                parent_object.on_state_change(old_state, new_state, pending_state)
        elif t == Gst.MessageType.ERROR:
            pipe.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            logger.error('GStreamer error from %s: %s' % (message.src.name, err))
            logger.error(f'GStreamer error debug: {str(debug)}')
            logger.error(f'GStreamer error message: {str(err.message)}')
            parent_object.error_message = err.message
            parent_object.report_update_to_user()
        elif t == Gst.MessageType.WARNING:
            pipe.set_state(Gst.State.NULL)
            err, debug = message.parse_warning()
            logger.warning('GStreamer warning from %s: %s' % (message.src.name, err))
            logger.warning(f'GStreamer warning debug: %s' % debug)
            logger.warning(f'GStreamer warning message: %s' % err.message)
            parent_object.error_message = err.message
            parent_object.report_update_to_user()
        elif t == Gst.MessageType.TAG:
            pass
            # logger.info 'MESSAGE:' + str(t)
            # logger.info('MESSAGE PARSED:' + message.get_structure().to_string())
        elif t == Gst.MessageType.LATENCY:
            logger.debug(f'Message from GStreamer: Latency from {str(message.src.get_name())}')
            # for x in dir(message.new_latency()): print(f"new_latency Contains: {x}")
            # for x in dir(message): print(f"Message Contains: {x}")
            # logger.info(f"New latency:{str(message.new_latency().parse_error())}")
            # logger.info(f"Message full:{str(message.src.message_full())}")
            # logger.info('MESSAGE PARSED:' + message.get_structure().to_string())
        elif t == Gst.MessageType.STREAM_STATUS:
            pass
        elif t == Gst.MessageType.ELEMENT:
            # Omit audio from 'level' element as it is very noisy:
            if message.src.get_factory().name != 'level':
                logger.debug(f'{str(message.src.get_name())} has a message:' + str(message.get_structure().to_string()))
        elif t == Gst.MessageType.DURATION_CHANGED:
            logger.debug(f'Duration changed to ' + str(pipe.query_duration(Gst.Format.TIME).duration) + 'ns')
            parent_object.report_update_to_user()
        elif t == Gst.MessageType.ASYNC_DONE:
            pass
            # logger.debug(f'Message from GStreamer: Async done')
        elif t == Gst.MessageType.STREAM_START:
            logger.debug('Message from GStreamer: Stream has now started.')
        elif t == Gst.MessageType.NEW_CLOCK:
            pass
            # logger.debug(f'Message from GStreamer: New clock.')
        elif t == Gst.MessageType.RESET_TIME:
            pass
        elif t == Gst.MessageType.NEED_CONTEXT:
            # logger.debug(f'Message from GStreamer: {str(message.src.get_name())} needs context')
            pass
        elif t == Gst.MessageType.HAVE_CONTEXT:
            logger.debug(f'Message from GStreamer: {str(message.src.get_name())} has context')
        elif t == Gst.MessageType.BUFFERING:
            buffering_percent = message.parse_buffering()
            logger.debug('%s has reported %s%% buffering: %s' %
                         (message.src.get_name(), buffering_percent, message.parse_buffering_stats()))
            if hasattr(parent_object, 'on_buffering'):
                parent_object.on_buffering(buffering_percent)
        elif t == Gst.MessageType.QOS:
            pass
            # Also can consider parse_qos_stats() and parse_qos_values()
            # logger.debug(f'Message from GStreamer: {str(message.src.get_name())} '
            #               'has sent QOS: {str(message.parse_qos())}')
        elif t == Gst.MessageType.PROPERTY_NOTIFY:
            parsed = message.parse_property_notify()
            logger.debug('Property notify: object="%s", property_name="%s", property_value="%s"' %
                         (parsed.object.name, parsed.property_name, parsed.property_value))
        elif t == Gst.MessageType.APPLICATION:
            # parsed = message.parse_application()
            struct = message.get_structure()
            logger.debug('parse_application: %s' % struct.get_value('text'))
            logger.debug('parse_application: %s' % struct.get_value('tex2t'))
        elif t in [Gst.MessageType.STREAM_COLLECTION, Gst.MessageType.DEVICE_ADDED, Gst.MessageType.STREAMS_SELECTED]:
            pass
        else:
            logger.info(f'GST UNHANDLED MESSAGE: {str(t)}: {str(message.src)}')

    bus = pipe.get_bus()
    bus.add_signal_watch()
    bus.connect('message', _on_message)
