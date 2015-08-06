#
# Copyright (c) 2015 ThoughtWorks, Inc.
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
from email.parser import Parser
import os
from mockito import verify, mock, when
import pkg_resources
from twisted.internet import defer
from twisted.trial.unittest import TestCase
from pixelated.adapter.mailstore import MailStore
from pixelated.adapter.mailstore.leap_mailstore import LeapMail
from pixelated.adapter.mailstore.searchable_mailstore import SearchableMailStore
from pixelated.adapter.search import SearchEngine


ANY_MAILBOX = 'INBOX'


class TestSearchableMailStore(TestCase):

    def setUp(self):
        super(TestSearchableMailStore, self).setUp()
        self.search_index = mock(mocked_obj=SearchEngine)
        self.delegate_mail_store = mock(mocked_obj=MailStore)
        self.store = SearchableMailStore(self.delegate_mail_store, self.search_index)

    @defer.inlineCallbacks
    def test_add_mail_delegates_to_mail_store_and_updates_index(self):
        mail = self._load_mail_from_file('mbox00000000')
        leap_mail = LeapMail('id', ANY_MAILBOX)
        when(self.delegate_mail_store).add_mail(ANY_MAILBOX, mail).thenReturn(defer.succeed(leap_mail))

        yield self.store.add_mail(ANY_MAILBOX, mail)

        verify(self.delegate_mail_store).add_mail(ANY_MAILBOX, mail)
        verify(self.search_index).index_mail(leap_mail)

    @defer.inlineCallbacks
    def test_add_mail_returns_stored_mail(self):
        mail = self._load_mail_from_file('mbox00000000')
        leap_mail = LeapMail('id', ANY_MAILBOX)
        when(self.delegate_mail_store).add_mail(ANY_MAILBOX, mail).thenReturn(defer.succeed(leap_mail))

        result = yield self.store.add_mail(ANY_MAILBOX, mail)

        self.assertEqual(leap_mail, result)

    @defer.inlineCallbacks
    def test_delete_mail_delegates_to_mail_store_and_updates_index(self):
        when(self.delegate_mail_store).delete_mail('mail id').thenReturn(defer.succeed(None))
        when(self.search_index).remove_from_index('mail id').thenReturn(defer.succeed(None))

        yield self.store.delete_mail('mail id')

        verify(self.delegate_mail_store).delete_mail('mail id')
        verify(self.search_index).remove_from_index('mail id')

    @defer.inlineCallbacks
    def test_update_mail_delegates_to_mail_store_and_updates_index(self):
        leap_mail = LeapMail('id', ANY_MAILBOX)

        yield self.store.update_mail(leap_mail)

        verify(self.delegate_mail_store).update_mail(leap_mail)
        verify(self.search_index).index_mail(leap_mail)

    @defer.inlineCallbacks
    def test_other_methods_are_delegated(self):
        mail = LeapMail('mail id', ANY_MAILBOX)
        when(self.delegate_mail_store).get_mail('mail id').thenReturn(defer.succeed(mail), defer.succeed(mail))
        result = yield self.store.get_mail('mail id')

        self.assertEqual(mail, result)

    def _load_mail_from_file(self, mail_file):
        mailset_dir = pkg_resources.resource_filename('test.unit.fixtures', 'mailset')
        mail_file = os.path.join(mailset_dir, 'new', mail_file)
        with open(mail_file) as f:
            mail = Parser().parse(f)
        return mail
