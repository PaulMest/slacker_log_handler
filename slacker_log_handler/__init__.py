import json
import traceback
from logging import Handler, CRITICAL, ERROR, WARNING, INFO, FATAL, DEBUG, NOTSET, Formatter

import six
import slacker

ERROR_COLOR = 'danger'  # color name is built in to Slack API
WARNING_COLOR = 'warning'  # color name is built in to Slack API
INFO_COLOR = '#439FE0'

COLORS = {
    CRITICAL: ERROR_COLOR,
    FATAL: ERROR_COLOR,
    ERROR: ERROR_COLOR,
    WARNING: WARNING_COLOR,
    INFO: INFO_COLOR,
    DEBUG: INFO_COLOR,
    NOTSET: INFO_COLOR,
}

DEFAULT_EMOJI = ':heavy_exclamation_mark:'


class NoStacktraceFormatter(Formatter):
    """
    By default the stacktrace will be formatted as part of the message.
    Since we want the stacktrace to be in the attachment of the Slack message,
     we need a custom formatter to leave it out of the message
    """

    def formatException(self, ei):
        return None


class SlackerLogHandler(Handler):
    def __init__(self, api_key, channel, stack_trace=True, username=None, icon_url=None, icon_emoji=None,
                 fail_silent=False, link_names=True):
        Handler.__init__(self)
        self.formatter = NoStacktraceFormatter()

        self.stack_trace = stack_trace
        self.fail_silent = fail_silent

        self.slacker = slacker.Slacker(api_key)
        self.username = username
        self.icon_url = icon_url
        self.icon_emoji = icon_emoji
        self.channel = channel
        self.link_names = link_names

        if not (self.channel.startswith('#') or self.channel.startswith('@')):
            raise ValueError('Invalid channel "{}". '
                             'It must start with "#" for a channel or "@" for a private message.'.format(self.channel))

    def build_msg(self, record):
        return six.text_type(self.format(record))

    def build_trace(self, record, fallback):
        trace = {
            'fallback': fallback,
            'color': COLORS.get(self.level, INFO_COLOR)
        }

        if record.exc_info:
            trace['text'] = '\n'.join(traceback.format_exception(*record.exc_info))

        return trace

    def emit(self, record):
        message = self.build_msg(record)

        if self.stack_trace:
            trace = self.build_trace(record, fallback=message)
            attachments = json.dumps([trace])
        else:
            attachments = None

        try:
            self.slacker.chat.post_message(
                text=message,
                channel=self.channel,
                username=self.username,
                icon_url=self.icon_url,
                icon_emoji=self.icon_emoji,
                attachments=attachments,
                link_names=self.link_names,
            )
        except slacker.Error as e:
            if self.fail_silent:
                pass
            else:
                raise e
