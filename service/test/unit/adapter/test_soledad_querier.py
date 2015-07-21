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
import json
import base64
import quopri
from uuid import uuid4
import pkg_resources

import pixelated.adapter.soledad.soledad_facade_mixin
from pixelated.adapter.soledad.soledad_querier import SoledadQuerier
from mockito import mock, when, any, unstub
from twisted.internet import defer


class SoledadQuerierTest(unittest.TestCase):

    def tearDown(self):
        unstub()

    @defer.inlineCallbacks
    def test_extract_parts(self):
        soledad = mock()
        bdoc = mock()
        bdoc.content = {'raw': 'esse papo seu ta qualquer coisa'}
        when(soledad).get_from_index('by-type-and-payloadhash', 'cnt', any(unicode)).thenReturn([bdoc])
        multipart_attachment_file = pkg_resources.resource_filename('test.unit.fixtures', 'multipart_attachment.json')
        with open(multipart_attachment_file) as f:
            hdoc = json.loads(f.read())
        querier = SoledadQuerier(soledad)

        parts = yield querier._extract_parts(hdoc)

        self.assertIn('alternatives', parts.keys())
        self.assertIn('attachments', parts.keys())
        self.assertEquals(2, len(parts['alternatives']))
        self.assertEquals(1, len(parts['attachments']))

        self.check_alternatives(parts)
        self.check_attachments(parts)

    def check_alternatives(self, parts):
        for alternative in parts['alternatives']:
            self.assertIn('headers', alternative)
            self.assertIn('content', alternative)

    def check_attachments(self, parts):
        for attachment in parts['attachments']:
            self.assertIn('headers', attachment)
            self.assertIn('ident', attachment)
            self.assertIn('name', attachment)

    @defer.inlineCallbacks
    def test_extract_part_without_headers(self):
        soledad = mock()
        bdoc = mock()
        bdoc.content = {'raw': 'esse papo seu ta qualquer coisa'}
        when(soledad).get_from_index('by-type-and-payloadhash', 'cnt', any(unicode)).thenReturn([bdoc])
        hdoc = {'multi': True, 'part_map': {'1': {'multi': False, 'phash': u'0400BEBACAFE'}}}
        querier = SoledadQuerier(soledad)

        parts = yield querier._extract_parts(hdoc)

        self.assertEquals(bdoc.content['raw'], parts['alternatives'][0]['content'])

    @defer.inlineCallbacks
    def test_extract_handles_missing_part_map(self):
        soledad = mock()
        hdoc = {u'multi': True,
                u'ctype': u'message/delivery-status',
                u'headers': [[u'Content-Description', u'Delivery report'], [u'Content-Type', u'message/delivery-status']],
                u'parts': 2,
                u'phash': None,
                u'size': 554}
        querier = SoledadQuerier(soledad)

        parts = yield querier._extract_parts(hdoc)

        self.assertEquals(0, len(parts['alternatives']))
        self.assertEquals(0, len(parts['attachments']))

    @defer.inlineCallbacks
    def test_attachment_base64(self):
        soledad = mock()
        bdoc = mock()
        bdoc.content = {'raw': base64.encodestring('esse papo seu ta qualquer coisa'), 'content-type': 'text/plain'}
        when(soledad).get_from_index('by-type-and-payloadhash', 'cnt', any(unicode)).thenReturn([bdoc])
        querier = SoledadQuerier(soledad)

        attachment = yield querier.attachment(u'0400BEBACAFE', 'base64')

        self.assertEquals('esse papo seu ta qualquer coisa', attachment['content'])

    @defer.inlineCallbacks
    def test_attachment_quoted_printable(self):
        soledad = mock()
        bdoc = mock()
        bdoc.content = {'raw': quopri.encodestring('esse papo seu ta qualquer coisa'), 'content-type': 'text/plain'}
        when(soledad).get_from_index('by-type-and-payloadhash', 'cnt', any(unicode)).thenReturn([bdoc])
        querier = SoledadQuerier(soledad)

        attachment = yield querier.attachment(u'0400BEBACAFE', 'quoted-printable')

        self.assertEquals('esse papo seu ta qualquer coisa', attachment['content'])

    @defer.inlineCallbacks
    def test_empty_or_null_queries_are_ignored(self):
        soledad = mock()
        when(soledad).get_from_index(any(), any(), any()).thenReturn(['nonempty', 'list'])
        querier = SoledadQuerier(soledad)

        test_parameters = ['', None]

        def call_with_bad_parameters(funct):
            deferreds = []
            for param in test_parameters:
                d = defer.maybeDeferred(funct, param)
                d.addCallback(self.assertFalse)
                deferreds.append(d)
            return defer.DeferredList(deferreds)

        yield call_with_bad_parameters(querier.get_all_flags_by_mbox)
        yield call_with_bad_parameters(querier.get_content_by_phash)
        yield call_with_bad_parameters(querier.get_flags_by_chash)
        yield call_with_bad_parameters(querier.get_header_by_chash)
        yield call_with_bad_parameters(querier.get_recent_by_mbox)
        yield call_with_bad_parameters(querier.idents_by_mailbox)
        yield call_with_bad_parameters(querier.get_mbox)

    def test_get_lastuid_broken(self):
        # FIXME this is completely out of sync with the new implementation
        soledad = mock()
        mbox = mock()
        mbox.content = {'lastuid': 0}
        when(soledad).get_from_index('by-type-and-mbox', 'mbox', 'INBOX').thenReturn([mbox])
        querier = SoledadQuerier(soledad)

        self.assertEquals(querier.get_lastuid(querier.get_mbox('INBOX')), 0)
        mbox.content = {'lastuid': 1}
        self.assertEquals(querier.get_lastuid(querier.get_mbox('INBOX')), 1)

    @defer.inlineCallbacks
    def test_get_lastuid(self):
        soledad = mock()
        mbox = mock()
        indexer = mock()
        mbox.content = {'uuid': str(uuid4())}
        when(soledad).get_from_index('by-type-and-mbox', 'mbox', 'INBOX').thenReturn(defer.succeed([mbox]))
        querier = SoledadQuerier(soledad)

        when(pixelated.adapter.soledad.soledad_facade_mixin).MailboxIndexer(soledad).thenReturn(indexer)
        when(indexer).create_table(any()).thenReturn(defer.succeed(None))
        when(indexer).get_last_uid(any()).thenReturn(defer.succeed(42))

        last_uid = (yield querier.get_lastuid('INBOX'))

        self.assertEquals(42, last_uid)

    @defer.inlineCallbacks
    def test_create_mail(self):
        soledad = mock()
        mbox = mock()
        mail = mock()
        indexer = mock()
        mbox.content = {'uuid': 'some uuid'}
        when(mail).get_for_save(next_uid=any(), mailbox='INBOX').thenReturn([])
        when(soledad).get_from_index('by-type-and-mbox', 'mbox', 'INBOX').thenReturn(defer.succeed([mbox]))
        querier = SoledadQuerier(soledad)
        when(querier).mail(any()).thenReturn([])

        when(pixelated.adapter.soledad.soledad_facade_mixin).MailboxIndexer(soledad).thenReturn(indexer)
        when(indexer).create_table(any()).thenReturn('')
        when(indexer).get_last_uid('some uuid').thenReturn(defer.succeed(42))

        mail_result = yield querier.create_mail(mail, 'INBOX')

        self.assertEquals([], mail_result)
