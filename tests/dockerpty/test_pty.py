# -*- coding: UTF-8 -*-
"""A suite of unit tests for the dockerpty.io.pty module"""
import unittest
from unittest.mock import patch, MagicMock

from ssl import SSLError

from container_shell.lib.dockerpty import pty, io


class TestWINCHHandler(unittest.TestCase):
    """A set of test cases for the WINCHHandler object"""
    def test_init(self):
        """``dockerpty.pty`` WINCHHandler requires a PTY object for init"""
        fake_pty = MagicMock()

        winch = pty.WINCHHandler(fake_pty)

        self.assertTrue(isinstance(winch, pty.WINCHHandler))

    @patch.object(pty.WINCHHandler, 'stop')
    @patch.object(pty.WINCHHandler, 'start')
    def test_context_mgr(self, fake_start, fake_stop):
        """``dockerpty.pty`` WINCHHandler support the with-statment"""
        fake_pty = MagicMock()

        with pty.WINCHHandler(fake_pty):
            pass

        self.assertTrue(fake_start.called)
        self.assertTrue(fake_stop.called)

    @patch.object(pty.signal, 'signal')
    def test_start(self, fake_signal):
        """``dockerpty.pty`` WINCHHandler sets the signal handler upon 'start'"""
        fake_signal.return_value = 'woot'
        fake_pty = MagicMock()
        winch = pty.WINCHHandler(fake_pty)

        winch.start()

        self.assertTrue(fake_signal.called)
        self.assertEqual(winch.original_handler, 'woot')

    @patch.object(pty.signal, 'signal')
    def test_stop(self, fake_signal):
        """``dockerpty.pyt WINCHHandler restores the signal handler upon 'stop'"""
        fake_pty = MagicMock()
        winch = pty.WINCHHandler(fake_pty)
        winch.original_handler = 'wooter'

        winch.stop()
        the_args, _ = fake_signal.call_args
        the_signal = the_args[0].name
        the_handler = the_args[1]
        expected_signal = 'SIGWINCH'
        expected_handler = 'wooter'

        self.assertEqual(the_signal, expected_signal)
        self.assertEqual(the_handler, expected_handler)


class TestRunOperation(unittest.TestCase):
    """A set of test cases for the RunOperation object"""
    def test_init(self):
        """``dockerpty.pty`` RunOperation init requires the docker client and container"""
        fake_client = MagicMock()
        fake_container = MagicMock()

        run_operation = pty.RunOperation(fake_client, fake_container)

        self.assertTrue(isinstance(run_operation, pty.RunOperation))

    def test_start(self):
        """``dockerpty.pty`` RunOperation 'start' returns a list of io.Pumps"""
        fake_client = MagicMock()
        fake_container = MagicMock()
        run_operation = pty.RunOperation(fake_client, fake_container)

        pumps = run_operation.start()
        all_pumps = all([x for x in pumps if isinstance(x, io.Pump)])

        self.assertTrue(all_pumps)
        self.assertTrue(len(pumps) > 0)

    def test_start_starts(self):
        """``dockerpty.pty`` RunOperation 'start' runs the container if needed"""
        fake_client = MagicMock()
        fake_container = MagicMock()
        run_operation = pty.RunOperation(fake_client, fake_container)
        run_operation._container_info = lambda : {'State' : {'Running' : False}}
        run_operation.sockets = lambda: (1,2,3)

        pumps = run_operation.start()

        self.assertTrue(fake_client.start.called)

    def test_israw(self):
        """``dockerpty.pty`` RunOperation 'israw' returns a boolean"""
        fake_client = MagicMock()
        fake_container = MagicMock()
        run_operation = pty.RunOperation(fake_client, fake_container)
        run_operation._container_info = lambda: {"Config" : {"Tty" : True}}

        answer = run_operation.israw()

        self.assertTrue(isinstance(answer, bool))

    def test_sockets(self):
        """``dockerpty.pty`` RunOperation 'sockets' returns a map object"""
        fake_client = MagicMock()
        fake_container = MagicMock()
        run_operation = pty.RunOperation(fake_client, fake_container)

        answer = run_operation.sockets()

        self.assertTrue(isinstance(answer, map))

    def test_sockets_demuxer(self):
        """``dockerpty.pty`` RunOperation 'sockets' uses an io.Demuxer if the container has no TTY"""
        fake_client = MagicMock()
        fake_container = MagicMock()
        run_operation = pty.RunOperation(fake_client, fake_container)
        run_operation._container_info = lambda: {'Config': {'Tty': False,
                                                            'AttachStdin' : MagicMock(),
                                                            'AttachStdout' : MagicMock(),
                                                            'AttachStderr' : MagicMock()}}

        things = list(run_operation.sockets())
        demuxers = [x for x in things if isinstance(x, io.Demuxer)]

        self.assertTrue(all(demuxers))
        self.assertEqual(len(demuxers), 3) # 1 for each stream

    def test_sockets_missing(self):
        """``dockerpty.pty`` RunOperation 'sockets' uses an io.Demuxer if the container has no TTY"""
        fake_client = MagicMock()
        fake_container = MagicMock()
        run_operation = pty.RunOperation(fake_client, fake_container)
        run_operation._container_info = lambda: {'Config': {'Tty': False,
                                                            'AttachStdin' : False,
                                                            'AttachStdout' : False,
                                                            'AttachStderr' : False}}

        output = list(run_operation.sockets())
        expected = [None, None, None]

        self.assertEqual(output, expected)

    def test_resize(self):
        """``dockerpty.pty`` RunOperation 'resize' resizes the container's PTY"""
        fake_client = MagicMock()
        fake_container = MagicMock()
        run_operation = pty.RunOperation(fake_client, fake_container)

        run_operation.resize(height=3, width=5)
        _, the_kwargs = fake_client.resize.call_args
        expected_kwargs = {'height': 3, 'width': 5}

        self.assertEqual(the_kwargs, expected_kwargs)

    def test_container_info(self):
        """```dockerpty.pty`` RunOperation '_container_info' inspects the container"""
        fake_client = MagicMock()
        fake_container = MagicMock()
        run_operation = pty.RunOperation(fake_client, fake_container)

        run_operation._container_info()
        the_args, _ = fake_client.inspect_container.call_args
        expected_args = (fake_container,)

        self.assertTrue(fake_client.inspect_container.called)
        self.assertEqual(the_args, expected_args)


class TestPseudoTerminal(unittest.TestCase):
    """A suite of test cases for the PseudoTerminal object"""
    def test_init(self):
        """``dockerpty.pty`` PseudoTerminal init takes the docker client and RunOperation object"""
        fake_client = MagicMock()
        fake_run_operation = MagicMock()

        pterminal = pty.PseudoTerminal(fake_client, fake_run_operation)

        self.assertTrue(isinstance(pterminal, pty.PseudoTerminal))

    def test_sockets(self):
        """``dockerpty.pty`` PseudoTerminal 'sockets' proxies to the RunOperation object"""
        fake_client = MagicMock()
        fake_run_operation = MagicMock()

        pty.PseudoTerminal(fake_client, fake_run_operation).sockets()

        self.assertTrue(fake_run_operation.sockets.called)

    @patch.object(pty.io, 'set_blocking')
    @patch.object(pty.PseudoTerminal, '_hijack_tty')
    @patch.object(pty, 'WINCHHandler')
    def test_start(self, fake_WINCHHandler, fake_hijack_tty, fake_set_blocking):
        """``dockerpty.pty`` PseudoTerminal 'start' hijacks the current TTY"""
        fake_client = MagicMock()
        fake_run_operation = MagicMock()
        fake_pump = MagicMock()
        fake_run_operation.start.return_value = [fake_pump]

        pty.PseudoTerminal(fake_client, fake_run_operation).start()

        self.assertTrue(fake_hijack_tty.called)

    def test_resize(self):
        """``dockerpty.pty`` PseudoTerminal 'resize' adjusts the containers PTY"""
        fake_client = MagicMock()
        fake_run_operation = MagicMock()
        fake_run_operation.israw.return_value = True

        pty.PseudoTerminal(fake_client, fake_run_operation).resize(size=(300,400))

        self.assertTrue(fake_run_operation.resize.called)

    def test_resize_israw(self):
        """``dockerpty.pty`` PseudoTerminal 'resize' doesn't resize anything if the local TTY is raw"""
        fake_client = MagicMock()
        fake_run_operation = MagicMock()
        fake_run_operation.israw.return_value = False

        pty.PseudoTerminal(fake_client, fake_run_operation).resize(size=(300,400))

        self.assertFalse(fake_run_operation.resize.called)

    def test_resize_ignore_ioerror(self):
        """``dockerpty.pty`` PseudoTerminal 'resize' ignores IOErrors"""
        fake_client = MagicMock()
        fake_run_operation = MagicMock()
        fake_run_operation.resize.side_effect = IOError('testing')
        fake_run_operation.israw.return_value = True

        pty.PseudoTerminal(fake_client, fake_run_operation).resize(size=(300,400))

    @patch.object(pty.io, 'select')
    @patch.object(pty.PseudoTerminal, '_get_stdin_pump')
    @patch.object(pty.tty, 'Terminal')
    def test_hijack_tty(self, fake_Terminal, fake_get_stdin_pump, fake_select):
        """``dockerpty.pty`` PseudoTerminal '_hijack_tty' runs until all Pumps are done"""
        fake_select.return_value = ([], [])
        fake_client = MagicMock()
        fake_run_operation = MagicMock()
        fake_pump = MagicMock()
        fake_pumps = [fake_pump]
        fake_select.return_value = ([fake_pump], [fake_pump])

        pty.PseudoTerminal(fake_client, fake_run_operation)._hijack_tty(fake_pumps)

        # It simply terminating is test enough ;)

    @patch.object(pty.sys.stdin, 'isatty')
    @patch.object(pty.io, 'select')
    @patch.object(pty.PseudoTerminal, '_get_stdin_pump')
    @patch.object(pty.tty, 'Terminal')
    def test_hijack_tty_not_tty(self, fake_Terminal, fake_get_stdin_pump, fake_select, fake_isatty):
        """``dockerpty.pty`` PseudoTerminal '_hijack_tty' terminates in non-TTY runtimes"""
        fake_select.return_value = ([], [])
        fake_client = MagicMock()
        fake_run_operation = MagicMock()
        fake_pump = MagicMock()
        fake_pumps = [fake_pump]
        fake_select.return_value = ([fake_pump], [fake_pump])
        fake_isatty.return_value = False

        pty.PseudoTerminal(fake_client, fake_run_operation)._hijack_tty(fake_pumps)

        # It simply terminating is test enough ;)

    @patch.object(pty.io, 'select')
    @patch.object(pty.PseudoTerminal, '_get_stdin_pump')
    @patch.object(pty.tty, 'Terminal')
    def test_hijack_tty_ok_ssl_error(self, fake_Terminal, fake_get_stdin_pump, fake_select):
        """``dockerpty.pty`` PseudoTerminal '_hijack_tty' can handle some SSL errors"""
        fake_select.return_value = ([], [])
        fake_client = MagicMock()
        fake_run_operation = MagicMock()
        fake_pump = MagicMock()
        ssl_error = SSLError()
        ssl_error.strerror = 'The operation did not complete'
        fake_pump.do_write.side_effect = [ssl_error, MagicMock()]
        fake_pumps = [fake_pump]
        fake_select.return_value = ([fake_pump], [fake_pump])

        pty.PseudoTerminal(fake_client, fake_run_operation)._hijack_tty(fake_pumps)


    @patch.object(pty.io, 'select')
    @patch.object(pty.PseudoTerminal, '_get_stdin_pump')
    @patch.object(pty.tty, 'Terminal')
    def test_hijack_tty_bad_ssl_error(self, fake_Terminal, fake_get_stdin_pump, fake_select):
        """``dockerpty.pty`` PseudoTerminal '_hijack_tty' raises if it catches an expected SSL error"""
        fake_select.return_value = ([], [])
        fake_client = MagicMock()
        fake_run_operation = MagicMock()
        fake_pump = MagicMock()
        ssl_error = SSLError()
        ssl_error.strerror = 'doh'
        fake_pump.do_write.side_effect = [ssl_error, MagicMock()]
        fake_pumps = [fake_pump]
        fake_select.return_value = ([fake_pump], [fake_pump])

        with self.assertRaises(SSLError):
            pty.PseudoTerminal(fake_client, fake_run_operation)._hijack_tty(fake_pumps)

    def test_get_stdin_pump(self):
        """``dockerpty.pty`` PseudoTerminal '_get_stdin_pump' returns the Pump object for stdin"""
        fake_pump = MagicMock()
        fake_pump.from_stream.fd.name = '<stdin>'
        fake_pumps = [fake_pump]

        answer = pty.PseudoTerminal._get_stdin_pump(fake_pumps)

        self.assertTrue(answer is fake_pump)

    def test_get_stdin_pump_runtime(self):
        """``dockerpty.pty`` PseudoTerminal '_get_stdin_pump' RuntimeError if a Pump for stdin doesn't exist"""
        fake_pump = MagicMock()
        fake_pump.from_stream.fd.name = '<stdout>'
        fake_pumps = [fake_pump]

        with self.assertRaises(RuntimeError):
            pty.PseudoTerminal._get_stdin_pump(fake_pumps)


if __name__ == '__main__':
    unittest.main()
