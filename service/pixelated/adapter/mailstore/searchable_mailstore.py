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
from twisted.internet import defer
from types import FunctionType
from pixelated.adapter.mailstore import MailStore


class SearchableMailStore(object):  # implementes MailStore

    def __init__(self, delegate, search_engine):
        self._delegate = delegate
        self._search_engine = search_engine

    @classmethod
    def _create_delegator(cls, method_name):
        def delegator(self, *args, **kw):
            return getattr(self._delegate, method_name)(*args, **kw)

        setattr(cls, method_name, delegator)

    @defer.inlineCallbacks
    def add_mail(self, mailbox_name, mail):
        stored_mail = yield self._delegate.add_mail(mailbox_name, mail)
        self._search_engine.index_mail(stored_mail)
        defer.returnValue(stored_mail)

    @defer.inlineCallbacks
    def delete_mail(self, mail_id):
        yield self._delegate.delete_mail(mail_id)
        self._search_engine.remove_from_index(mail_id)

    @defer.inlineCallbacks
    def update_mail(self, mail):
        yield self._delegate.update_mail(mail)
        self._search_engine.index_mail(mail)

    def __getattr__(self, name):
        """
        Acts like method missing. If a method of MailStore is not implemented in this class,
        a delegate method is created.

        :param name: attribute name
        :return: method or attribute
        """
        methods = ([key for key, value in MailStore.__dict__.items() if type(value) == FunctionType])

        if name in methods:
            SearchableMailStore._create_delegator(name)
            return super(SearchableMailStore, self).__getattribute__(name)
        else:
            raise NotImplemented('No attribute %s' % name)
