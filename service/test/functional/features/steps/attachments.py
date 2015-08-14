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
from email.mime.application import MIMEApplication
from time import sleep
from leap.mail.mail import Message
from common import *
from test.support.integration import MailBuilder
from behave import given
from crochet import wait_for
from uuid import uuid4
from email.MIMEMultipart import MIMEMultipart
from email.mime.text import MIMEText


@given(u'I have a mail with an attachment in my inbox')
def add_mail_with_attachment_impl(context):
    subject = 'Hi! This the subject %s' % uuid4()
    mail = build_mail_with_attachment(subject)
    load_mail_into_soledad(context, mail)
    context.last_subject = subject


def build_mail_with_attachment(subject):
    mail = MIMEMultipart()
    mail['Subject'] = subject
    mail.attach(MIMEText(u'a utf8 message', _charset='utf-8'))
    attachment = MIMEApplication('pretend to be binary attachment data')
    attachment.add_header('Content-Disposition', 'attachment', filename='filename.txt')
    mail.attach(attachment)

    return mail


@wait_for(timeout=10.0)
def load_mail_into_soledad(context, mail):
    return context.client.mail_store.add_mail('INBOX', mail.as_string())


@then(u'I see the mail has an attachment')
def step_impl(context):
    attachments_list = find_elements_by_css_selector(context, '.attachmentsArea li')
    assert len(attachments_list) == 1
