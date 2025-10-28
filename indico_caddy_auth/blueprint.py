# This file is part of the Indico plugins.
# Copyright (C) 2025 FortranCon operators
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.

from indico.core.plugins import IndicoPluginBlueprint

from indico_caddy_auth.controllers import RHCaddyAuthValidate


blueprint = IndicoPluginBlueprint('caddy_auth', 'indico_caddy_auth')

blueprint.add_url_rule('/auth/validate', 'validate', RHCaddyAuthValidate, methods=('GET',))