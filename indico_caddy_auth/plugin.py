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

        # Parse environment variables once and store as class attributes
        import os

        # Read trusted domains from env var (comma-separated string)
        trusted_domains_str = os.environ.get('INDICO_CADDY_AUTH_TRUSTED_DOMAINS', '')
        self.trusted_domains = [domain.strip() for domain in trusted_domains_str.split(',') if domain.strip()]

        self._patch_multipass_redirect_validation()

    def get_blueprints(self):
        return blueprint

    def _patch_multipass_redirect_validation(self):
        """Monkeypatch multipass to allow cross-subdomain redirects for configured trusted domains."""
        # If no trusted domains configured, skip the monkeypatch entirely
        if not self.trusted_domains:
            self.logger.info(
                'No CADDY_AUTH_TRUSTED_DOMAINS configured - using default Flask-Multipass redirect validation'
            )
            return

        # Log the trusted domains for verification
        self.logger.info('Allowing redirects to domains: %s', ', '.join(self.trusted_domains))

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
                for domain in self.trusted_domains:
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
