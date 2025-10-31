# This file is part of the Indico plugins.
# Copyright (C) 2025 FortranCon operators
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.

from urllib.parse import urljoin, urlsplit

from flask import make_response, redirect, request, session

from indico.core.config import config
from indico.web.rh import RH


class RHCaddyAuthValidate(RH):
    """Authentication validation endpoint for Caddy forward_auth."""

    def _process(self):
        user = session.user
        if not user:
            # Build return URL from Caddy's forwarded headers
            original_proto = request.headers.get('X-Forwarded-Proto', urlsplit(config.BASE_URL).scheme)
            # X-Forwarded-Host can contain multiple hosts,for Indico to work it must have the BASE_URL
            # get it, filter it, fallback to BASE_URL host
            original_host = next(
                (
                    host
                    for host in request.headers.get('X-Forwarded-Host', '').split(',')
                    if host != urlsplit(config.BASE_URL).hostname
                ),
                urlsplit(config.BASE_URL).hostname,
            )
            original_uri = request.headers.get('X-Forwarded-Uri', '')

            if original_uri:
                query_string = request.query_string.decode('utf-8')
                if query_string:
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
        response.headers['Remote-User'] = user.email
        return response
