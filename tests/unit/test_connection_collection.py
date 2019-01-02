import time, pytest, inspect, sys
sys.path.append('.')
import brave.session
from brave.inputs.input import Input
from brave.connections import ConnectionCollection
from brave.exceptions import InvalidConfiguration

def test_connection_collection():
    session = brave.session.init()
    cc = session.connections
    input = session.inputs.add(type='test_video')
    output1 = session.outputs.add(type='local')
    output2 = session.outputs.add(type='image')
    mixer = session.mixers.add()

    connection1 = cc.add(input, mixer)
    assert connection1.source == input
    assert connection1.dest == mixer

    connection2 = cc.add(mixer, output1)
    assert connection2.source == mixer
    assert connection2.dest == output1

    connection3 = cc.add(input, output2)
    assert connection3.source == input
    assert connection3.dest == output2

    subtest_cannot_link_output_to_more_than_one_source(cc, input, output2)
    subtest_can_find_source_and_dest(cc, input, mixer, output1, connection1, connection2, connection3)
    subtest_cannot_link_the_wrong_way(cc, input, mixer, output1)
    subtest_can_access_connections_from_input(session, input, [connection1, connection3])
    subtest_can_access_source_connections_from_mixer(session, mixer, [connection1])
    subtest_can_access_dest_connections_from_mixer(session, mixer, [connection2])
    subtest_can_access_connections_from_output(session, output1, connection2)
    subtest_can_access_connections_from_output(session, output2, connection3)


def test_creating_connection_from_input_to_mixer():
    session = brave.session.init()
    mixer = session.mixers.add()
    input = session.inputs.add(type='test_video')
    assert mixer.connection_for_source(input) == None
    connection1 = mixer.connection_for_source(input, create_if_not_made=True)
    assert connection1.source == input
    assert connection1.dest == mixer
    connection1_copy = mixer.connection_for_source(input, create_if_not_made=True)
    assert connection1_copy == connection1


def test_creating_connection_from_mixer_to_output():
    session = brave.session.init()
    mixer = session.mixers.add()
    output = session.outputs.add(type='local')
    connection2 = output.connection_for_source(mixer, create_if_not_made=True)
    assert connection2.source == mixer
    assert connection2.dest == output
    connection2_copy = output.connection_for_source(mixer, create_if_not_made=True)
    assert connection2_copy == connection2


def subtest_cannot_link_output_to_more_than_one_source(cc, input, output2):
    with pytest.raises(InvalidConfiguration):
        cc.add(input, output2)

def subtest_can_find_source_and_dest(cc, input, mixer, output1, connection1, connection2, connection3):
    assert cc.get_first_for_source(input) == connection1
    assert cc.get_first_for_source(mixer) == connection2
    assert cc.get_first_for_source(output1) == None

    assert cc.get_all_for_source(input) == [connection1, connection3]
    assert cc.get_all_for_source(mixer) == [connection2]
    assert cc.get_all_for_source(output1) == []

    assert cc.get_first_for_dest(input) == None
    assert cc.get_first_for_dest(mixer) == connection1
    assert cc.get_first_for_dest(output1) == connection2

    assert cc.get_all_for_dest(input) == []
    assert cc.get_all_for_dest(mixer) == [connection1]
    assert cc.get_all_for_dest(output1) == [connection2]


def subtest_cannot_link_the_wrong_way(cc, input, mixer, output):
    with pytest.raises(ValueError):
        cc.add(mixer, input)

    with pytest.raises(ValueError):
        cc.add(output, mixer)

def subtest_can_access_connections_from_input(session, input, connections):
    assert input.dest_connections() == connections

def subtest_can_access_source_connections_from_mixer(session, mixer, connections):
    assert mixer.source_connections() == connections

def subtest_can_access_dest_connections_from_mixer(session, mixer, connections):
    assert mixer.dest_connections() == connections

def subtest_can_access_connections_from_output(session, output, connection):
    assert output.source_connection() == connection
