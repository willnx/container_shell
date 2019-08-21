# -*- coding: UTF-8 -*-
"""A suite of unit tests for the dockerpty.tty module"""
import unittest
from unittest.mock import patch, MagicMock

from container_shell.lib.dockerpty import tty as dtty # avoid name collision with stdlib tty


class FakeObj:
    """Simplies some unit tests"""
    def __repr__(self):
        return 'FakeObj'


class TestSize(unittest.TestCase):
    """A suite of test cases for the ``size`` function"""
    def test_not_a_tty(self):
        """``dockerpty.tty`` 'size' returns None if the supplied file descriptor is not a TTY"""
        fake_fd = MagicMock()

        answer = dtty.size(fake_fd)

        self.assertTrue(answer is None)

    @patch.object(dtty.os, 'isatty')
    def test_exception(self, fake_isatty):
        """``dockerpty.tty`` 'size' returns None if an Exception occurs"""
        fake_fd = MagicMock()
        fake_isatty.return_value = False

        answer = dtty.size(fake_fd)

        self.assertTrue(answer is None)


class TestTerminal(unittest.TestCase):
    """A suite of test cases for the ``Terminal`` object"""
    def test_init(self):
        """``dockerpty.tty`` Terminal object requires a file descriptor for init"""
        fake_fd = MagicMock()

        terminal = dtty.Terminal(fake_fd)

        self.assertTrue(isinstance(terminal, dtty.Terminal))

    @patch.object(dtty.Terminal, 'start')
    @patch.object(dtty.Terminal, 'stop')
    def test_context_manager(self, fake_stop, fake_start):
        """``dockerpty.tty`` Terminal object supports the with-statement"""
        fake_fd = MagicMock()

        with dtty.Terminal(fake_fd):
            pass

        self.assertTrue(fake_start.called)
        self.assertTrue(fake_stop.called)

    def test_israw(self):
        """``dockerpty.tty`` Terminal 'israw' returns the 'raw' attribute"""
        fake_fd = MagicMock()
        terminal = dtty.Terminal(fake_fd)

        self.assertTrue(terminal.israw() is terminal.raw)

    @patch.object(dtty.termios, 'tcgetattr')
    @patch.object(dtty.tty, 'setraw')
    def test_start(self, fake_setraw, fake_tcgetattr):
        """``dockerpty.tty`` Terminal 'start' sets the file descripter to a raw TTY"""
        fake_fd = MagicMock()
        terminal = dtty.Terminal(fake_fd)
        terminal.start()

        self.assertTrue(fake_setraw.called)

    @patch.object(dtty.termios, 'tcsetattr')
    def test_stop(self, fake_tcsetattr):
        """``dockerpty.tty`` Terminal 'stop' resets the terminal attributes"""
        fake_fd = MagicMock()
        terminal = dtty.Terminal(fake_fd)
        terminal.original_attributes = 'wooter'
        terminal.stop()

        self.assertTrue(fake_tcsetattr.called)

    def test_repr(self):
        """``dockerpty.tty`` Terminal has a handy repr"""
        fake_fd = FakeObj()
        terminal = dtty.Terminal(fake_fd)

        the_repr = '{}'.format(terminal)
        expected = 'Terminal(FakeObj, raw=True)'

        self.assertEqual(the_repr, expected)









if __name__ == '__main__':
    unittest.main()
