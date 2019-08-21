# -*- coding: UTF-8 -*-
"""A suite of unit tests for the dockerpty.__init__.py module"""
import unittest
from unittest.mock import patch, MagicMock

from container_shell.lib import dockerpty


class TestInit(unittest.TestCase):
    """A suite of test cases for the __init__ of dockerpty"""
    @patch.object(dockerpty, 'PseudoTerminal')
    @patch.object(dockerpty, 'RunOperation')
    def test_start_runoperation(self, fake_RunOperation, fake_PseudoTerminal):
        """"``dockerpty.start`` calls 'RunOperation'"""
        fake_client = MagicMock()
        fake_container = MagicMock()
        dockerpty.start(fake_client, fake_container)

        self.assertTrue(fake_RunOperation.called)

    @patch.object(dockerpty, 'PseudoTerminal')
    @patch.object(dockerpty, 'RunOperation')
    def test_start_pseudoterminal(self, fake_RunOperation, fake_PseudoTerminal):
        """"``dockerpty.start`` calls 'PseudoTerminal'"""
        fake_client = MagicMock()
        fake_container = MagicMock()
        dockerpty.start(fake_client, fake_container)

        self.assertTrue(fake_PseudoTerminal.called)


if __name__ == '__main__':
    unittest.main()
