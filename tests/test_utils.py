# -*- coding: UTF-8 -*-
"""A suite of unit tests for the ``utils.py`` module"""
import unittest
from unittest.mock import patch

import logging

from container_shell.lib import utils


class TestUtils(unittest.TestCase):
    """A suite of tests cases for the functions in the ``utils`` module"""
    def test_skip_container(self):
        """``utils`` the 'skip_container' function returns a boolean"""
        result = utils.skip_container('bob', '')

        self.assertTrue(isinstance(result, bool))

    def test_skip_container_true(self):
        """``utils`` the 'skip_container' function returns True if the user is in the list"""
        result = utils.skip_container('bob', 'admin,bob,liz')

        self.assertTrue(result)

    def test_skip_container_false(self):
        """``utils`` the 'skip_container' function returns False if the user is *not* in the list"""
        result = utils.skip_container('sam', 'admin,bob,liz')

        self.assertFalse(result)

    @patch.object(utils.sys, 'stderr')
    def test_printerr(self, fake_stderr):
        """``utils`` 'printerr' appends a newline char"""
        msg = 'hello world!'
        utils.printerr(msg)

        the_args, _ = fake_stderr.write.call_args
        written_msg = the_args[0]
        expected = '{}\n'.format(msg)

        self.assertEqual(written_msg, expected)

    @patch.object(utils.sys, 'stderr')
    def test_printerr_flush(self, fake_stderr):
        """``utils`` 'printerr' flushes stderr upon write"""
        utils.printerr('hello world!')

        self.assertTrue(fake_stderr.flush.called)

    def test_get_logger(self):
        """``utils`` 'get_logger' Returns a logging object"""
        logger = utils.get_logger(name='foo',
                                 location='/tmp/junk.txt',
                                 max_size=102400,
                                 max_count=3)

        self.assertTrue(isinstance(logger, logging.Logger))


if __name__ == '__main__':
    unittest.main()
