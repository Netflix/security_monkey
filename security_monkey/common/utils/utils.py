#     Copyright 2014 Netflix, Inc.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
"""
.. module: security_monkey.common.utils.utils
    :platform: Unix
    :synopsis: Utility methods pasted and bastardized from all over the place. Can probably be removed completely.

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from security_monkey import app, mail
from flask_mail import Message
import boto
import traceback

prims = [int, str, unicode, bool, type(None)]


def sub_list(l):
    r = []

    for i in l:
        if type(i) in prims:
            r.append(i)
        elif type(i) is list:
            r.append(sub_list(i))
        elif type(i) is dict:
            r.append(sub_dict(i))
        else:
            print "Unknown Type: {}".format(type(i))
    r = sorted(r)
    return r


def sub_dict(d):
    r = {}
    for k in d:
        if type(d[k]) in prims:
            r[k] = d[k]
        elif type(d[k]) is list:
            r[k] = sub_list(d[k])
        elif type(d[k]) is dict:
            r[k] = sub_dict(d[k])
        else:
            print "Unknown Type: {}".format(type(d[k]))
    return r


def send_email(subject=None, recipients=[], html=""):
    """
    Given a message, will send that message over SES or SMTP, depending upon how the app is configured.
    """
    plain_txt_email = "Please view in a mail client that supports HTML."
    if app.config.get('EMAILS_USE_SMTP'):
        try:
            with app.app_context():
                msg = Message(subject, recipients=recipients)
                msg.body = plain_txt_email
                msg.html = html
                mail.send(msg)
            app.logger.debug("Emailed {} - {} ".format(recipients, subject))
        except Exception, e:
            m = "Failed to send failure message with subject: {}\n{} {}".format(subject, Exception, e)
            app.logger.debug(m)
            app.logger.warn(traceback.format_exc())

    else:
        ses = boto.connect_ses()
        for email in recipients:
            try:
                ses.send_email(app.config.get('MAIL_DEFAULT_SENDER'), subject, html, email, format="html")
                app.logger.debug("Emailed {} - {} ".format(email, subject))
            except Exception, e:
                m = "Failed to send failure message with subject: {}\n{} {}".format(subject, Exception, e)
                app.logger.debug(m)
