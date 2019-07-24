#
# Copyright (C) 2019 EfficiOS Inc.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; only version 2
# of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#

from bt2 import value
import collections
import unittest
import copy
import bt2


class _MyIter(bt2._UserMessageIterator):
    def __init__(self, self_output_port):
        self._build_meta()
        self._at = 0

    def _build_meta(self):
        self._tc = self._component._create_trace_class()
        self._t = self._tc()
        self._sc = self._tc.create_stream_class(supports_packets=True)
        self._ec = self._sc.create_event_class(name='salut')
        self._my_int_ft = self._tc.create_signed_integer_field_class(32)
        payload_ft = self._tc.create_structure_field_class()
        payload_ft += [('my_int', self._my_int_ft)]
        self._ec.payload_field_type = payload_ft
        self._stream = self._t.create_stream(self._sc)
        self._packet = self._stream.create_packet()

    def _create_event(self, value):
        ev = self._ec()
        ev.payload_field['my_int'] = value
        ev.packet = self._packet
        return ev


class GraphTestCase(unittest.TestCase):
    def setUp(self):
        self._graph = bt2.Graph()

    def tearDown(self):
        del self._graph

    def test_create_empty(self):
        graph = bt2.Graph()

    def test_add_component_user_cls(self):
        class MySink(bt2._UserSinkComponent):
            def _consume(self):
                pass

            def _graph_is_configured(self):
                pass

        comp = self._graph.add_component(MySink, 'salut')
        self.assertEqual(comp.name, 'salut')

    def test_add_component_gen_cls(self):
        class MySink(bt2._UserSinkComponent):
            def _consume(self):
                pass

            def _graph_is_configured(self):
                pass

        comp = self._graph.add_component(MySink, 'salut')
        assert comp
        comp2 = self._graph.add_component(comp.cls, 'salut2')
        self.assertEqual(comp2.name, 'salut2')

    def test_add_component_params(self):
        comp_params = None

        class MySink(bt2._UserSinkComponent):
            def __init__(self, params):
                nonlocal comp_params
                comp_params = params

            def _consume(self):
                pass

            def _graph_is_configured(self):
                pass

        params = {'hello': 23, 'path': '/path/to/stuff'}
        comp = self._graph.add_component(MySink, 'salut', params)
        self.assertEqual(params, comp_params)
        del comp_params

    def test_add_component_invalid_cls_type(self):
        with self.assertRaises(TypeError):
            self._graph.add_component(int, 'salut')

    def test_add_component_invalid_logging_level_type(self):
        class MySink(bt2._UserSinkComponent):
            def _consume(self):
                pass

            def _graph_is_configured(self):
                pass

        with self.assertRaises(TypeError):
            self._graph.add_component(MySink, 'salut', logging_level='yo')

    def test_add_component_invalid_logging_level_value(self):
        class MySink(bt2._UserSinkComponent):
            def _consume(self):
                pass

            def _graph_is_configured(self):
                pass

        with self.assertRaises(ValueError):
            self._graph.add_component(MySink, 'salut', logging_level=12345)

    def test_add_component_logging_level(self):
        class MySink(bt2._UserSinkComponent):
            def _consume(self):
                pass

            def _graph_is_configured(self):
                pass

        comp = self._graph.add_component(
            MySink, 'salut', logging_level=bt2.LoggingLevel.DEBUG
        )
        self.assertEqual(comp.logging_level, bt2.LoggingLevel.DEBUG)

    def test_connect_ports(self):
        class MyIter(bt2._UserMessageIterator):
            def __next__(self):
                raise bt2.Stop

        class MySource(bt2._UserSourceComponent, message_iterator_class=MyIter):
            def __init__(self, params):
                self._add_output_port('out')

        class MySink(bt2._UserSinkComponent):
            def __init__(self, params):
                self._add_input_port('in')

            def _consume(self):
                raise bt2.Stop

            def _graph_is_configured(self):
                pass

        src = self._graph.add_component(MySource, 'src')
        sink = self._graph.add_component(MySink, 'sink')

        conn = self._graph.connect_ports(
            src.output_ports['out'], sink.input_ports['in']
        )
        self.assertTrue(src.output_ports['out'].is_connected)
        self.assertTrue(sink.input_ports['in'].is_connected)
        self.assertEqual(src.output_ports['out'].connection.addr, conn.addr)
        self.assertEqual(sink.input_ports['in'].connection.addr, conn.addr)

    def test_connect_ports_invalid_direction(self):
        class MyIter(bt2._UserMessageIterator):
            def __next__(self):
                raise bt2.Stop

        class MySource(bt2._UserSourceComponent, message_iterator_class=MyIter):
            def __init__(self, params):
                self._add_output_port('out')

        class MySink(bt2._UserSinkComponent):
            def __init__(self, params):
                self._add_input_port('in')

            def _consume(self):
                raise bt2.Stop

            def _graph_is_configured(self):
                pass

        src = self._graph.add_component(MySource, 'src')
        sink = self._graph.add_component(MySink, 'sink')

        with self.assertRaises(TypeError):
            conn = self._graph.connect_ports(
                sink.input_ports['in'], src.output_ports['out']
            )

    def test_add_interrupter(self):
        class MyIter(bt2._UserMessageIterator):
            def __next__(self):
                raise TypeError

        class MySource(bt2._UserSourceComponent, message_iterator_class=MyIter):
            def __init__(self, params):
                self._add_output_port('out')

        class MySink(bt2._UserSinkComponent):
            def __init__(self, params):
                self._add_input_port('in')

            def _consume(self):
                next(self._msg_iter)

            def _graph_is_configured(self):
                self._msg_iter = self._create_input_port_message_iterator(
                    self._input_ports['in']
                )

        # add two interrupters, set one of them
        interrupter1 = bt2.Interrupter()
        interrupter2 = bt2.Interrupter()
        self._graph.add_interrupter(interrupter1)
        src = self._graph.add_component(MySource, 'src')
        sink = self._graph.add_component(MySink, 'sink')
        self._graph.connect_ports(src.output_ports['out'], sink.input_ports['in'])
        self._graph.add_interrupter(interrupter2)

        with self.assertRaises(bt2._Error):
            self._graph.run()

        interrupter2.set()

        with self.assertRaises(bt2.TryAgain):
            self._graph.run()

        interrupter2.reset()

        with self.assertRaises(bt2._Error):
            self._graph.run()

    # Test that Graph.run() raises bt2.Interrupted if the graph gets
    # interrupted during execution.
    def test_interrupt_while_running(self):
        class MyIter(_MyIter):
            def __next__(self):
                return self._create_stream_beginning_message(self._stream)

        class MySource(bt2._UserSourceComponent, message_iterator_class=MyIter):
            def __init__(self, params):
                self._add_output_port('out')

        class MySink(bt2._UserSinkComponent):
            def __init__(self, params):
                self._add_input_port('in')

            def _consume(self):
                # Pretend that somebody asynchronously interrupted the graph.
                nonlocal graph
                graph.interrupt()
                return next(self._msg_iter)

            def _graph_is_configured(self):
                self._msg_iter = self._create_input_port_message_iterator(
                    self._input_ports['in']
                )

        graph = self._graph
        up = self._graph.add_component(MySource, 'down')
        down = self._graph.add_component(MySink, 'up')
        self._graph.connect_ports(up.output_ports['out'], down.input_ports['in'])

        with self.assertRaises(bt2.TryAgain):
            self._graph.run()

    def test_run(self):
        class MyIter(_MyIter):
            def __next__(self):
                if self._at == 9:
                    raise StopIteration

                if self._at == 0:
                    msg = self._create_stream_beginning_message(self._stream)
                elif self._at == 1:
                    msg = self._create_packet_beginning_message(self._packet)
                elif self._at == 7:
                    msg = self._create_packet_end_message(self._packet)
                elif self._at == 8:
                    msg = self._create_stream_end_message(self._stream)
                else:
                    msg = self._create_event_message(self._ec, self._packet)

                self._at += 1
                return msg

        class MySource(bt2._UserSourceComponent, message_iterator_class=MyIter):
            def __init__(self, params):
                self._add_output_port('out')

        class MySink(bt2._UserSinkComponent):
            def __init__(self, params):
                self._input_port = self._add_input_port('in')
                self._at = 0

            def _consume(comp_self):
                msg = next(comp_self._msg_iter)

                if comp_self._at == 0:
                    self.assertIsInstance(msg, bt2._StreamBeginningMessage)
                elif comp_self._at == 1:
                    self.assertIsInstance(msg, bt2._PacketBeginningMessage)
                elif comp_self._at >= 2 and comp_self._at <= 6:
                    self.assertIsInstance(msg, bt2._EventMessage)
                    self.assertEqual(msg.event.cls.name, 'salut')
                elif comp_self._at == 7:
                    self.assertIsInstance(msg, bt2._PacketEndMessage)
                elif comp_self._at == 8:
                    self.assertIsInstance(msg, bt2._StreamEndMessage)

                comp_self._at += 1

            def _graph_is_configured(self):
                self._msg_iter = self._create_input_port_message_iterator(
                    self._input_port
                )

        src = self._graph.add_component(MySource, 'src')
        sink = self._graph.add_component(MySink, 'sink')
        conn = self._graph.connect_ports(
            src.output_ports['out'], sink.input_ports['in']
        )
        self._graph.run()

    def test_run_again(self):
        class MyIter(_MyIter):
            def __next__(self):
                if self._at == 3:
                    raise bt2.TryAgain

                if self._at == 0:
                    msg = self._create_stream_beginning_message(self._stream)
                elif self._at == 1:
                    msg = self._create_packet_beginning_message(self._packet)
                elif self._at == 2:
                    msg = self._create_event_message(self._ec, self._packet)

                self._at += 1
                return msg

        class MySource(bt2._UserSourceComponent, message_iterator_class=MyIter):
            def __init__(self, params):
                self._add_output_port('out')

        class MySink(bt2._UserSinkComponent):
            def __init__(self, params):
                self._input_port = self._add_input_port('in')
                self._at = 0

            def _consume(comp_self):
                msg = next(comp_self._msg_iter)
                if comp_self._at == 0:
                    self.assertIsInstance(msg, bt2._StreamBeginningMessage)
                elif comp_self._at == 1:
                    self.assertIsInstance(msg, bt2._PacketBeginningMessage)
                elif comp_self._at == 2:
                    self.assertIsInstance(msg, bt2._EventMessage)
                    raise bt2.TryAgain
                else:
                    pass

                comp_self._at += 1

            def _graph_is_configured(self):
                self._msg_iter = self._create_input_port_message_iterator(
                    self._input_port
                )

        src = self._graph.add_component(MySource, 'src')
        sink = self._graph.add_component(MySink, 'sink')
        conn = self._graph.connect_ports(
            src.output_ports['out'], sink.input_ports['in']
        )

        with self.assertRaises(bt2.TryAgain):
            self._graph.run()

    def test_run_error(self):
        raised_in_sink = False

        class MyIter(_MyIter):
            def __next__(self):
                # If this gets called after the sink raised an exception, it is
                # an error.
                nonlocal raised_in_sink
                assert raised_in_sink is False

                if self._at == 0:
                    msg = self._create_stream_beginning_message(self._stream)
                elif self._at == 1:
                    msg = self._create_packet_beginning_message(self._packet)
                elif self._at == 2 or self._at == 3:
                    msg = self._create_event_message(self._ec, self._packet)
                else:
                    raise bt2.TryAgain
                self._at += 1
                return msg

        class MySource(bt2._UserSourceComponent, message_iterator_class=MyIter):
            def __init__(self, params):
                self._add_output_port('out')

        class MySink(bt2._UserSinkComponent):
            def __init__(self, params):
                self._input_port = self._add_input_port('in')
                self._at = 0

            def _consume(comp_self):
                msg = next(comp_self._msg_iter)
                if comp_self._at == 0:
                    self.assertIsInstance(msg, bt2._StreamBeginningMessage)
                elif comp_self._at == 1:
                    self.assertIsInstance(msg, bt2._PacketBeginningMessage)
                elif comp_self._at == 2:
                    self.assertIsInstance(msg, bt2._EventMessage)
                elif comp_self._at == 3:
                    nonlocal raised_in_sink
                    raised_in_sink = True
                    raise RuntimeError('error!')

                comp_self._at += 1

            def _graph_is_configured(self):
                self._msg_iter = self._create_input_port_message_iterator(
                    self._input_port
                )

        src = self._graph.add_component(MySource, 'src')
        sink = self._graph.add_component(MySink, 'sink')
        conn = self._graph.connect_ports(
            src.output_ports['out'], sink.input_ports['in']
        )

        with self.assertRaises(bt2._Error):
            self._graph.run()

    def test_listeners(self):
        class MyIter(bt2._UserMessageIterator):
            def __next__(self):
                raise bt2.Stop

        class MySource(bt2._UserSourceComponent, message_iterator_class=MyIter):
            def __init__(self, params):
                self._add_output_port('out')
                self._add_output_port('zero')

        class MySink(bt2._UserSinkComponent):
            def __init__(self, params):
                self._add_input_port('in')

            def _consume(self):
                raise bt2.Stop

            def _graph_is_configured(self):
                pass

            def _port_connected(self, port, other_port):
                self._add_input_port('taste')

        def port_added_listener(component, port):
            nonlocal calls
            calls.append((port_added_listener, component, port))

        def ports_connected_listener(
            upstream_component, upstream_port, downstream_component, downstream_port
        ):
            nonlocal calls
            calls.append(
                (
                    ports_connected_listener,
                    upstream_component,
                    upstream_port,
                    downstream_component,
                    downstream_port,
                )
            )

        calls = []
        self._graph.add_port_added_listener(port_added_listener)
        self._graph.add_ports_connected_listener(ports_connected_listener)
        src = self._graph.add_component(MySource, 'src')
        sink = self._graph.add_component(MySink, 'sink')
        self._graph.connect_ports(src.output_ports['out'], sink.input_ports['in'])

        self.assertEqual(len(calls), 5)

        self.assertIs(calls[0][0], port_added_listener)
        self.assertEqual(calls[0][1].name, 'src')
        self.assertEqual(calls[0][2].name, 'out')

        self.assertIs(calls[1][0], port_added_listener)
        self.assertEqual(calls[1][1].name, 'src')
        self.assertEqual(calls[1][2].name, 'zero')

        self.assertIs(calls[2][0], port_added_listener)
        self.assertEqual(calls[2][1].name, 'sink')
        self.assertEqual(calls[2][2].name, 'in')

        self.assertIs(calls[3][0], port_added_listener)
        self.assertEqual(calls[3][1].name, 'sink')
        self.assertEqual(calls[3][2].name, 'taste')

        self.assertIs(calls[4][0], ports_connected_listener)
        self.assertEqual(calls[4][1].name, 'src')
        self.assertEqual(calls[4][2].name, 'out')
        self.assertEqual(calls[4][3].name, 'sink')
        self.assertEqual(calls[4][4].name, 'in')

    def test_invalid_listeners(self):
        class MyIter(bt2._UserMessageIterator):
            def __next__(self):
                raise bt2.Stop

        class MySource(bt2._UserSourceComponent, message_iterator_class=MyIter):
            def __init__(self, params):
                self._add_output_port('out')
                self._add_output_port('zero')

        class MySink(bt2._UserSinkComponent):
            def __init__(self, params):
                self._add_input_port('in')

            def _consume(self):
                raise bt2.Stop

            def _graph_is_configured(self):
                pass

            def _port_connected(self, port, other_port):
                self._add_input_port('taste')

        with self.assertRaises(TypeError):
            self._graph.add_port_added_listener(1234)
        with self.assertRaises(TypeError):
            self._graph.add_ports_connected_listener(1234)

    def test_raise_in_component_init(self):
        class MySink(bt2._UserSinkComponent):
            def __init__(self, params):
                raise ValueError('oops!')

            def _consume(self):
                raise bt2.Stop

            def _graph_is_configured(self):
                pass

        graph = bt2.Graph()

        with self.assertRaises(bt2._Error):
            graph.add_component(MySink, 'comp')

    def test_raise_in_port_added_listener(self):
        class MySink(bt2._UserSinkComponent):
            def __init__(self, params):
                self._add_input_port('in')

            def _consume(self):
                raise bt2.Stop

            def _graph_is_configured(self):
                pass

        def port_added_listener(component, port):
            raise ValueError('oh noes!')

        graph = bt2.Graph()
        graph.add_port_added_listener(port_added_listener)

        with self.assertRaises(bt2._Error):
            graph.add_component(MySink, 'comp')

    def test_raise_in_ports_connected_listener(self):
        class MyIter(bt2._UserMessageIterator):
            def __next__(self):
                raise bt2.Stop

        class MySource(bt2._UserSourceComponent, message_iterator_class=MyIter):
            def __init__(self, params):
                self._add_output_port('out')

        class MySink(bt2._UserSinkComponent):
            def __init__(self, params):
                self._add_input_port('in')

            def _consume(self):
                raise bt2.Stop

            def _graph_is_configured(self):
                pass

        def ports_connected_listener(
            upstream_component, upstream_port, downstream_component, downstream_port
        ):
            raise ValueError('oh noes!')

        graph = bt2.Graph()
        graph.add_ports_connected_listener(ports_connected_listener)
        up = graph.add_component(MySource, 'down')
        down = graph.add_component(MySink, 'up')

        with self.assertRaises(bt2._Error):
            graph.connect_ports(up.output_ports['out'], down.input_ports['in'])
