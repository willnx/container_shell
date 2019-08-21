# -*- coding: UTF-8 -*-
"""A suite of unit test for the dockerpty.io module"""
import errno
import unittest
from unittest.mock import patch, MagicMock

from container_shell.lib.dockerpty import  io


class FakeObj:
    """Used to create fake objects for unit tests"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    def __repr__(self):
        return 'some object'


class FakeFD(FakeObj):
    """Used to mock a file descriptor object during unit tests"""
    def __repr__(self):
        return 'some file descriptor object'


class TestFunctions(unittest.TestCase):
    """A suite of test cases for the functions in dockerpty.io"""
    @patch.object(io.fcntl, 'fcntl')
    def test_set_blocking(self, fake_fcntl):
        """``dockerpty.io`` 'set_blocking' returns if the original status was blocking"""
        fake_fcntl.return_value = 32796
        fake_fd = MagicMock()

        original_status = io.set_blocking(fake_fd)
        expected = True

        self.assertTrue(original_status is expected)

    @patch.object(io.fcntl, 'fcntl')
    def test_set_blocking_false(self, fake_fcntl):
        """`dockerpty.io` 'set_blocking' uses the correct flag to make an fd non-blocking"""
        fake_fcntl.return_value = 32796
        fake_fd = MagicMock()

        original_status = io.set_blocking(fake_fd, blocking=False)
        set_args = fake_fcntl.call_args_list[1]
        blocking_flag = set_args[0][2]
        expected = 34844

        self.assertEqual(blocking_flag, expected)

    @patch.object(io.builtin_select, 'select')
    def test_select(self, fake_select):
        """``dockerpty.io`` 'select' only returns the read and write lists"""
        reads, writes, errors = [], [], []
        fake_select.return_value = [reads, writes, errors]

        output = io.select(MagicMock(), MagicMock())
        expected = [reads, writes]

        self.assertEqual(output, expected)

    @patch.object(io.builtin_select, 'select')
    def test_select_interrupts(self, fake_select):
        """``dockerpty.io`` 'select' gracefully handles SIGINT signals"""
        error = OSError()
        error.errno = errno.EINTR
        fake_select.side_effect = [error]

        output = io.select(MagicMock(), MagicMock())
        expected = ([], [])

        self.assertEqual(output, expected)

    @patch.object(io.builtin_select, 'select')
    def test_select_error(self, fake_select):
        """``dockerpty.io`` 'select' raises unexpected errors"""
        fake_select.side_effect = [RuntimeError('testing')]

        with self.assertRaises(RuntimeError):
            io.select(MagicMock(), MagicMock())


class TestStream(unittest.TestCase):
    """A suite of test cases for the Stream object"""
    def test_recoverable_errors(self):
        """``dockerpty.io`` The errors Stream can recover from hasn't changed"""
        expected = [errno.EINTR, errno.EDEADLK, errno.EWOULDBLOCK,]
        self.assertEqual(io.Stream.ERRNO_RECOVERABLE, expected)

    def test_init(self):
        """``dockerpty.io`` the Stream object only requires a file descriptor"""
        fake_fd = MagicMock()
        stream = io.Stream(fake_fd)

        self.assertTrue(isinstance(stream, io.Stream))

    def test_fileno(self):
        """``dockerpty.io`` Stream.fileno proxies to the file descriptor"""
        fake_fd = MagicMock()
        fake_fd.fileno.return_value = 9

        output = io.Stream(fake_fd).fileno()
        expected = 9

        self.assertEqual(output, expected)

    @patch.object(io, 'set_blocking')
    def test_set_blocking(self, fake_set_blocking):
        """``dockerpty.io`` Stream.set_blocking can manually set blocking on a the file descriptor"""
        fake_fd = FakeFD()

        io.Stream(fake_fd).set_blocking(56)

        self.assertTrue(fake_set_blocking.called)

    @patch.object(io, 'set_blocking')
    def test_set_blocking_fd(self, fake_set_blocking):
        """``dockerpty.io`` Stream.set_blocking proxies the call to the file descriptor if possible"""
        fake_fd = MagicMock()

        io.Stream(fake_fd).set_blocking(56)

        self.assertTrue(fake_fd.setblocking.called)

    def test_read(self):
        """``dockerpty.io`` Stream.read returns N number of bytes from the stream"""
        fake_fd = MagicMock()
        fake_fd.recv.return_value = 'some bytes'

        output = io.Stream(fake_fd).read()
        expected = 'some bytes'

        self.assertEqual(output, expected)

    @patch.object(io.os, 'read')
    def test_read_os(self, fake_read):
        """``dockerpty.io`` Stream.read calls to os.read if the file descriptor has no 'recv' attribute"""
        fake_fd = FakeFD()
        fake_fd.fileno = lambda : 56
        fake_read.return_value = 'yay, bytes!'

        output = io.Stream(fake_fd).read()
        expected = 'yay, bytes!'

        self.assertEqual(output, expected)

    def test_read_error(self):
        """``dockerpty.io`` Stream.read raises unexpected errors"""
        fake_fd = MagicMock()
        error = OSError()
        error.errno = 8965
        fake_fd.recv.side_effect = [error]

        with self.assertRaises(OSError):
            io.Stream(fake_fd).read()

    def test_write(self):
        """``dockerpty.io`` Stream.write adds to the buffer, then calls 'do_write'"""
        data = b'yay bites!'
        fake_fd = MagicMock()
        fake_do_write = MagicMock()
        stream = io.Stream(fake_fd)
        stream.do_write = fake_do_write

        stream.write(data)

        self.assertEqual(stream.buffer, data)
        self.assertTrue(fake_do_write.called)

    def test_write_return(self):
        """``dockerpty.io`` Stream.write returns the number of bytes written"""
        data = b'yay bites!'
        fake_fd = MagicMock()
        fake_do_write = MagicMock()
        stream = io.Stream(fake_fd)
        stream.do_write = fake_do_write

        bytes_written = stream.write(data)
        expected = len(data)

        self.assertEqual(bytes_written, expected)

    def test_write_ignore(self):
        """``dockerpty.io`` Stream.write adds to the buffer, then calls 'do_write'"""
        data = b''
        fake_fd = MagicMock()
        fake_do_write = MagicMock()
        stream = io.Stream(fake_fd)
        stream.do_write = fake_do_write

        bytes_written = stream.write(data)
        expected = 0

        self.assertEqual(bytes_written, expected)

    def test_do_write(self):
        """``dockerpty.io`` Stream.do_write returns how many bytes were written"""
        fake_fd = MagicMock()
        fake_fd.send.return_value = 93

        stream = io.Stream(fake_fd)
        written = stream.do_write()
        expected = 93

        self.assertEqual(written, expected)

    def test_do_write_closes(self):
        """``dockerpty.io`` Stream.do_write closes when requested after writing"""
        fake_fd = MagicMock()
        fake_fd.send.return_value = 3
        fake_close = MagicMock()
        stream = io.Stream(fake_fd)
        stream.close = fake_close
        stream.close_requested = True

        stream.do_write()

        self.assertTrue(fake_close.called)

    @patch.object(io.os, 'write')
    def test_do_write_os_write(self, fake_write):
        """``dockerpty.io`` Stream.do_write calls os.write when the file descriptor has no 'send' method"""
        fake_fd = FakeFD()
        fake_fd.fileno = lambda: 32

        io.Stream(fake_fd).do_write()

        self.assertTrue(fake_write.called)

    def test_do_write_error(self):
        """``dockerpty.io`` Stream.do_write closes when requested after writing"""
        fake_fd = MagicMock()
        error = OSError()
        error.errno = 2346
        fake_fd.send.side_effect = [error]

        with self.assertRaises(OSError):
            io.Stream(fake_fd).do_write()

    def test_needs_write(self):
        """``dockerpty.io`` Stream.needs_write Returns True when there's data in the buffer"""
        fake_fd = MagicMock()
        stream = io.Stream(fake_fd)
        stream.buffer = b'some data'

        self.assertTrue(stream.needs_write())

    def test_needs_write_false(self):
        """``dockerpty.io`` Stream.needs_write Returns False when buffer is empty"""
        fake_fd = MagicMock()
        stream = io.Stream(fake_fd)

        self.assertFalse(stream.needs_write())

    def test_close(self):
        """``dockerpty.io`` Stream.close closes the file descriptor"""
        fake_fd = MagicMock()
        stream = io.Stream(fake_fd)

        stream.close()

        self.assertTrue(stream.closed)
        self.assertTrue(fake_fd.close.called)

    @patch.object(io.os, 'close')
    def test_close_os(self, fake_close):
        """``dockerpty.io`` Stream.close closes the file descriptor even if the fd had no 'close' attribute"""
        fake_fd = FakeFD()
        fake_fd.fileno = lambda: 3445
        stream = io.Stream(fake_fd)

        stream.close()

        self.assertTrue(stream.closed)
        self.assertTrue(fake_close.called)

    def test_repr(self):
        """``dockerpty.io`` Stream has a handy __repr__"""
        fake_fd = FakeFD()
        stream = io.Stream(fake_fd)

        the_repr = '{}'.format(stream)
        expected = 'Stream(some file descriptor object)'

        self.assertEqual(the_repr, expected)


class TestDemuxer(unittest.TestCase):
    """A suite of test cases for the Demuxer object"""
    def test_init(self):
        """``dockerpty.io`` Demuxer only requires a Stream for init"""
        fake_stream = MagicMock()

        demuxer = io.Demuxer(fake_stream)

        self.assertTrue(isinstance(demuxer, io.Demuxer))

    def test_fileno(self):
        """``dockerpty.io`` Demuxer leverages the Stream for 'fileno'"""
        fake_stream = MagicMock()
        fake_stream.fileno.return_value = 345

        fileno = io.Demuxer(fake_stream).fileno()
        expected = 345

        self.assertEqual(expected, fileno)

    def test_set_blocking(self):
        """``dockerpty.io`` Demuxer leverages the Stream for 'set_blocking'"""
        fake_stream = MagicMock()

        io.Demuxer(fake_stream).set_blocking('some value')

        self.assertTrue(fake_stream.set_blocking.called)

    def test_read(self):
        """``dockerpty.io`` Demuxer reads N bytes of data, and returns it"""
        fake_stream = MagicMock()
        fake_stream.read.return_value = b'some data!'
        demuxer = io.Demuxer(fake_stream)
        demuxer._next_packet_size = lambda x: 10

        data = demuxer.read()
        expected = b'some data!'

        self.assertEqual(data, expected)

    def test_read_zero(self):
        """``dockerpty.io`` Demuxer returns None if there's no data to read"""
        fake_stream = MagicMock()
        demuxer = io.Demuxer(fake_stream)
        demuxer._next_packet_size = lambda x: 0

        output = demuxer.read()

        self.assertTrue(output is None)

    def test_read_closed_stream(self):
        """``dockerpty.io`` Demuxer returns as much as it can if the stream closes"""
        fake_stream = MagicMock()
        fake_stream.read.side_effect = [b'some', b'']
        demuxer = io.Demuxer(fake_stream)
        demuxer._next_packet_size = lambda x: 10

        output = demuxer.read()
        expected = b'some'

        self.assertEqual(output, expected)

    def test_write(self):
        """``dockerpty.io`` Demuxer proxies writes to the Stream object"""
        fake_stream = MagicMock()
        demuxer = io.Demuxer(fake_stream)

        demuxer.write(b'some data')

        self.assertTrue(fake_stream.write.called)

    def test_needs_write(self):
        """``dockerpty.io`` Demuxer proxies to the Stream for 'needs_write'"""
        fake_stream = MagicMock()
        demuxer = io.Demuxer(fake_stream)

        demuxer.needs_write()

        self.assertTrue(fake_stream.needs_write.called)

    def test_needs_write_no_attr(self):
        """``dockerpty.io`` Demuxer return False if the Stream object has no 'needs_write' attribute"""
        fake_stream = FakeObj()
        demuxer = io.Demuxer(fake_stream)

        answer = demuxer.needs_write()

        self.assertFalse(answer)

    def test_do_write(self):
        """``dockerpty.io`` Demuxer proxies to the Stream for 'do_write'"""
        fake_stream = MagicMock()
        demuxer = io.Demuxer(fake_stream)

        demuxer.do_write()

        self.assertTrue(fake_stream.do_write.called)

    def test_do_write_no_attr(self):
        """``dockerpty.io`` Demuxer return False if the Stream object has no 'do_write' attribute"""
        fake_stream = FakeObj()
        demuxer = io.Demuxer(fake_stream)

        answer = demuxer.do_write()

        self.assertFalse(answer)

    def test_close(self):
        """``dockerpty.io`` Demuxer proxies to Stream to close it"""
        fake_stream = MagicMock()

        io.Demuxer(fake_stream).close()

        self.assertTrue(fake_stream.close.called)

    def test_repr(self):
        """``dockerpty.io`` Demuxer has a handy repr"""
        fake_stream = FakeObj()
        demuxer = io.Demuxer(fake_stream)

        the_repr = '{}'.format(demuxer)
        expected = 'Demuxer(some object)'

        self.assertEqual(the_repr, expected)

    def test_next_packet_size(self):
        """``dockerpty.io`` Demuxer pulls the payload size from the header from Docker"""
        fake_stream = MagicMock()
        fake_stream.read.return_value = b'12345678'
        demuxer = io.Demuxer(fake_stream)

        answer = demuxer._next_packet_size()
        expected = 0

        self.assertEqual(answer, expected)

    def test_next_packet_size_remain(self):
        """``dockerpty.io`` Demuxer _next_packet_size handles remainders"""
        fake_stream = MagicMock()
        fake_stream.read.return_value = b'12345678'
        demuxer = io.Demuxer(fake_stream)
        demuxer.remain = 2

        answer = demuxer._next_packet_size()
        expected = 0

        self.assertEqual(answer, expected)

    def test_next_packet_size_zero_read(self):
        """``dockerpty.io`` Demuxer '_next_packet_size' returns zero if nothing is read from the Stream"""
        fake_stream = MagicMock()
        fake_stream.read.return_value = b''
        demuxer = io.Demuxer(fake_stream)

        answer = demuxer._next_packet_size()
        expected = 0

        self.assertEqual(answer, expected)


class TestPump(unittest.TestCase):
    """A suite of test cases for the Pump object"""
    def test_init(self):
        """``dockerpty.io`` Pump requires two Streams for init"""
        fake_from_stream = MagicMock()
        fake_to_stream = MagicMock()

        pump = io.Pump(fake_from_stream, fake_to_stream)

        self.assertTrue(isinstance(pump, io.Pump))

    def test_fileno(self):
        """``dockerpty.io`` Pump.fileno returns the fileno of the 'from_stream'"""
        fake_from_stream = MagicMock()
        fake_from_stream.fileno.return_value = 9001
        fake_to_stream = MagicMock()
        pump = io.Pump(fake_from_stream, fake_to_stream)

        fileno = pump.fileno()
        expected = 9001

        self.assertEqual(fileno, expected)

    def test_set_blocking(self):
        """``dockerpty.io`` Pump.set_blocking adjusts the 'from_stream''"""
        fake_from_stream = MagicMock()
        fake_to_stream = MagicMock()
        pump = io.Pump(fake_from_stream, fake_to_stream)

        pump.set_blocking('some value')

        self.assertTrue(fake_from_stream.set_blocking.called)

    def test_flush(self):
        """``dockerpty.io`` Pump.flush returns the number of bytes written into the 'to_stream'"""
        fake_from_stream = MagicMock()
        fake_from_stream.read.return_value = b'some bytes'
        fake_to_stream = MagicMock()
        fake_to_stream.write = lambda x: len(x)
        pump = io.Pump(fake_from_stream, fake_to_stream)

        written = pump.flush()
        expected = 10

        self.assertEqual(written, expected)

    def test_flush_eof(self):
        """``dockerpty.io`` Pump.flush returns None when the 'from_stream' reaches EOF"""
        fake_from_stream = MagicMock()
        fake_from_stream.read.return_value = b''
        fake_to_stream = MagicMock()
        pump = io.Pump(fake_from_stream, fake_to_stream)

        written = pump.flush()

        self.assertTrue(written is None)
        self.assertTrue(pump.eof)

    def test_flush_error(self):
        """``dockerpty.io`` Pump.flush raises errors"""
        error = OSError()
        error.errno = 8965
        fake_from_stream = MagicMock()
        fake_from_stream.read.side_effect = [error]
        fake_to_stream = MagicMock()
        pump = io.Pump(fake_from_stream, fake_to_stream)

        with self.assertRaises(OSError):
            pump.flush()

    def test_is_done(self):
        """``dockerpty.io`` Pump.is_done returns False if the to_stream.needs_write is True"""
        fake_from_stream = MagicMock()
        fake_to_stream = MagicMock()
        fake_to_stream.needs_write.return_value = True
        pump = io.Pump(fake_from_stream, fake_to_stream)

        self.assertFalse(pump.is_done())

    def test_is_done_true(self):
        """``dockerpty.io`` Pump.is_done returns True if the to_stream.needs_write is False and the pump reaches EOF"""
        fake_from_stream = MagicMock()
        fake_to_stream = MagicMock()
        fake_to_stream.needs_write.return_value = False
        pump = io.Pump(fake_from_stream, fake_to_stream)
        pump.eof = True

        self.assertTrue(pump.is_done())


    def test_repr(self):
        """``dockerpty.io`` Pump has a handy repr"""
        fake_from_stream = FakeObj()
        fake_to_stream = FakeObj()
        pump = io.Pump(fake_from_stream, fake_to_stream)

        the_repr = '{}'.format(pump)
        expected = 'Pump(from=some object, to=some object)'

        self.assertEqual(the_repr, expected)


if __name__ == '__main__':
    unittest.main()
