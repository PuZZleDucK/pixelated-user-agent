#
# Copyright (c) 2014 ThoughtWorks, Inc.
#
# Pixelated is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pixelated is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Pixelated. If not, see <http://www.gnu.org/licenses/>.
from twisted.trial import unittest

from pixelated.adapter.model.mail import PixelatedMail
from pixelated.adapter.services.mailbox import Mailbox
from mockito import mock, when, verify
from test.support import test_helper
from twisted.internet import defer


class PixelatedMailboxTest(unittest.TestCase):
    def setUp(self):
        self.querier = mock()
        self.search_engine = mock()
        self.mailbox = Mailbox('INBOX', self.querier, self.search_engine)

    def test_remove_message_from_mailbox(self):
        mail = PixelatedMail.from_soledad(*test_helper.leap_mail(), soledad_querier=self.querier)
        when(self.querier).mail(1).thenReturn(mail)

        self.mailbox.remove(1)

        verify(self.querier).remove_mail(mail)

    @defer.inlineCallbacks
    def test_fresh_mailbox_checking_lastuid(self):
        when(self.querier).get_lastuid('INBOX').thenReturn(0)
        self.assertTrue(self.mailbox.fresh)
        when(self.querier).get_lastuid('INBOX').thenReturn(1)
        self.assertFalse((yield self.mailbox.fresh))
