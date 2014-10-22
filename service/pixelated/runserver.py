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

import os
import os.path
import crochet
from flask import Flask
from leap.common.events import server as events_server
from pixelated.config import app_factory
import pixelated.config.args as input_args
import pixelated.bitmask_libraries.register as leap_register
import pixelated.config.reactor_manager as reactor_manager
import pixelated.support.ext_protobuf  # monkey patch for protobuf in OSX


app = Flask(__name__, static_url_path='', static_folder=app_factory.get_static_folder())


def setup():
    try:
        args = input_args.parse()
        debug_enabled = args.debug or os.environ.get('DEBUG', False)
        reactor_manager.start_reactor(logging=debug_enabled)
        crochet.setup()

        events_server.ensure_server(port=8090)

        app.config.from_pyfile(args.config)

        if args.register:
            server_name = app.config['LEAP_SERVER_NAME']
            leap_register.register_new_user(args.register, server_name)
        else:
            app_factory.create_app(debug_enabled, app)
    finally:
        reactor_manager.stop_reactor_on_exit()


if __name__ == '__main__':
    setup()