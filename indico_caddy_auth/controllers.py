# This file is part of the Indico plugins.
# Copyright (C) 2025 FortranCon operators
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.

from urllib.parse import urljoin

from flask import make_response, redirect, request, session

from indico.core.config import config
from indico.web.rh import RH


class RHCaddyAuthValidate(RH):
    """Authentication validation endpoint for Caddy forward_auth."""

    def _process(self):
        user = session.user
        if not user:
            # Build return URL from Caddy's forwarded headers
            original_uri = request.headers.get('X-Forwarded-Uri', '')
            original_host = request.headers.get('X-Forwarded-Host', 'chat.fortrancon.org')
            original_proto = request.headers.get('X-Forwarded-Proto', 'https')

            if original_uri:
                # Include query parameters in the return URL
                query_string = request.query_string.decode('utf-8')
                if query_string:
                    # If we have query parameters, add them to the original URI
                    separator = '&' if '?' in original_uri else '?'
                    full_uri = f'{original_uri}{separator}{query_string}'
                else:
                    full_uri = original_uri

                return_url = f'{original_proto}://{original_host}{full_uri}'
                login_url = urljoin(config.BASE_URL, f'login?next={return_url}')
            else:
                login_url = urljoin(config.BASE_URL, 'login')

            return redirect(login_url)

        # User authenticated - return success with Remote-User header
        response = make_response('', 200)
        response.headers['X-Forwarded-Remote-User'] = user.email
        return response
