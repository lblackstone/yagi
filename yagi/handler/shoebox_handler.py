import json
import logging
import os

import notification_utils
from shoebox import roll_manager
import simport

import yagi.config
import yagi.handler
import yagi.utils

LOG = logging.getLogger(__name__)


class ShoeboxHandler(yagi.handler.BaseHandler):
    """The shoebox handler doesn't really fit with
       yagi persistence interface currently. We'll need
       to refactor one or the other to clean it up.
    """

    def __init__(self, app=None, queue_name=None):
        super(ShoeboxHandler, self).__init__(app, queue_name)
        # Don't use interpolation from ConfigParser ...
        self.config = dict(yagi.config.config.items('shoebox', raw=True))
        roll_checker_str = self.config['roll_checker']
        self.roll_checker = simport.load(roll_checker_str)(**self.config)
        self.working_directory = self.config.get('working_directory', '.')
        self.destination_folder = self.config.get('destination_folder', '.')
        for d in [self.working_directory, self.destination_folder]:
            if not os.path.isdir(d):
                os.makedirs(d)
        template=self.config.get('filename_template',
                                 'events_%Y_%m_%d_%X_%f.dat')
        cb = simport.load(self.config['callback'])(**self.config)
        self.roll_manager = roll_manager.WritingRollManager(template,
                                self.roll_checker, self.working_directory,
                                archive_callback=cb)

    def handle_messages(self, messages, env):
        # TODO(sandy): iterate_payloads filters messages first ... not
        # sure if we want that for raw archiving.
        for payload in self.iterate_payloads(messages, env):
            metadata = {}
            json_event = json.dumps(payload,
                                    cls=notification_utils.DateTimeEncoder)
            LOG.debug("shoebox writing payload: %s" % str(payload))
            self.roll_manager.write(metadata, json_event)
