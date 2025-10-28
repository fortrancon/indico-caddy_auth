# This file is part of the Indico plugins.
# Copyright (C) 2025 FortranCon operators
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.

from indico.core.plugins import IndicoPlugin

from indico_caddy_auth import _
from indico_caddy_auth.blueprint import blueprint


class CaddyAuthPlugin(IndicoPlugin):
    """Caddy Forward Auth

    Provides authentication validation endpoint for Caddy forward_auth.
    """

    def init(self):
        super().init()

    def get_blueprints(self):
        return blueprint