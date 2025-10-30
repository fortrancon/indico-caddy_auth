# This file is part of the Indico plugins.
# Copyright (C) 2025 FortranCon operators
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.

from urllib.parse import urlparse

from indico.core.plugins import IndicoPlugin

from indico_caddy_auth.blueprint import blueprint


class CaddyAuthPlugin(IndicoPlugin):
    """Caddy Forward Auth

    Provides authentication validation endpoint for Caddy forward_auth.
    """

    def init(self):
        super().init()
        self._patch_multipass_redirect_validation()

    def get_blueprints(self):
        return blueprint

    def _patch_multipass_redirect_validation(self):
        """Monkeypatch multipass to allow cross-subdomain redirects for configured trusted domains."""
        from indico.core.config import config

        # Get trusted domains from config
        trusted_domains = getattr(config, 'CADDY_AUTH_TRUSTED_DOMAINS', [])

        # If no trusted domains configured, skip the monkeypatch entirely
        if not trusted_domains:
            self.logger.info(
                'No CADDY_AUTH_TRUSTED_DOMAINS configured - using default Flask-Multipass redirect validation'
            )
            return

        # Log the trusted domains for verification
        self.logger.info('Allowing redirects to domains: %s', ', '.join(trusted_domains))

        # Apply the monkeypatch only if we have trusted domains
        from indico.core.auth import multipass

        # Store the original method
        original_validate_next_url = multipass.validate_next_url

        def validate_next_url_with_trusted_domains(url):
            """Enhanced validate_next_url that allows redirects to configured trusted domains."""
            # First try the original validation (allows same host and relative URLs)
            if original_validate_next_url(url):
                return True

            # Check against configured trusted domains
            try:
                parsed = urlparse(url)

                # Check against configured trusted domains
                for domain in trusted_domains:
                    # Support both exact matches and wildcard subdomains
                    if parsed.netloc == domain:
                        return True

                    if domain.startswith('.') and parsed.netloc.endswith(domain):
                        return True

                return False
            except Exception:
                return False

        # Apply the monkeypatch
        multipass.validate_next_url = validate_next_url_with_trusted_domains
