# Indico Caddy Auth Plugin

This plugin provides an authentication validation endpoint for Caddy's `forward_auth` directive, allowing you to use Indico as an authentication backend for other services.

## Features

- Provides `/auth/validate` endpoint for Caddy forward_auth
- Handles authentication redirects with proper return URLs
- Integrates seamlessly with Indico's session management
- Returns `Remote-User` header for authenticated users
- **Monkeypatches Flask-Multipass** to allow cross-subdomain redirects for configured trusted domains
- **Configures session cookies for cross-subdomain authentication** via `SESSION_COOKIE_DOMAIN_OVERRIDE`
- Preserves query parameters through the authentication flow
- **Configurable trusted domains** via `CADDY_AUTH_TRUSTED_DOMAINS` setting

## Installation

1. Install the plugin:
```bash
cd caddy_auth
pip install -e .
```

2. Enable the plugin in your `indico.conf`:
```python
PLUGINS = {'caddy_auth'}
```

3. Configure the plugin via environment variables:
```bash
# Configure domains that are allowed for redirects after login (comma-separated)
export INDICO_CADDY_AUTH_TRUSTED_DOMAINS="chat.fortrancon.org"

# REQUIRED: Configure session cookie domain for cross-subdomain authentication
# This allows Indico session cookies to work when forwarded from other subdomains
export INDICO_CADDY_AUTH_SESSION_COOKIE_DOMAIN_OVERRIDE=".fortrancon.org"
```

**Domain Configuration Examples:**
- `fortrancon.org` - Allows only fortrancon.org exactly
- `chat.fortrancon.org` - Allows only chat.fortrancon.org exactly
- `.trusted.org` - Allows *.trusted.org (note the leading dot)

**Important**: The session cookie domain `.fortrancon.org` is required for cross-subdomain authentication to work. Without it, Indico sessions remain tied to `events.fortrancon.org` and can't be validated when forwarded from `chat.fortrancon.org`.

4. Restart Indico

## Usage with Caddy

Configure Caddy to use the auth endpoint. For Zulip, only the SSO login endpoint needs forward_auth:

```caddyfile
events.fortrancon.org {
    reverse_proxy localhost:8080
}

chat.fortrancon.org {
    # Only protect the Zulip SSO login endpoint
    handle /accounts/login/sso* {
        forward_auth localhost:8080 {
            uri /auth/validate
            copy_headers Remote-User
            header_up Host events.fortrancon.org
            header_up Cookie {http.request.header.Cookie}
        }
        reverse_proxy localhost:9991
    }

    # All other requests go directly to Zulip
    reverse_proxy localhost:9991
}
```

**Important Notes**:
- Use `localhost:8080` (direct backend) for `forward_auth` to avoid Caddy loops
- The `header_up Host events.fortrancon.org` line ensures Indico accepts the auth request
- The `header_up Cookie {http.request.header.Cookie}` line forwards session cookies so Indico can validate authentication
- Only `/accounts/login/sso*` needs authentication - Zulip handles its own sessions afterward
- Query parameters from the original request are preserved in redirect URLs

## How It Works

### Zulip SSO Flow

1. User visits `chat.fortrancon.org` and clicks "Login with SSO"
2. Browser redirects to `chat.fortrancon.org/accounts/login/sso`
3. Caddy forward_auth calls `localhost:8080/auth/validate` with user's cookies
4. If user is authenticated in Indico: Returns 200 with `Remote-User` header → Zulip logs user in
5. If user is not authenticated: Returns redirect to Indico login page with return URL
6. User logs into Indico on `events.fortrancon.org` → **session cookie set with domain `.fortrancon.org`**
7. User gets redirected back to `/accounts/login/sso`
8. Caddy calls `/auth/validate` again with the cross-subdomain session cookies
9. Plugin validates the session and returns 200 with `Remote-User` header
10. Zulip completes the login

### General Flow (for other services)

1. User visits protected resource (e.g., `other.fortrancon.org`)
2. Caddy calls `localhost:8080/auth/validate`
3. If user is authenticated: Returns 200 with `Remote-User` header
4. If user is not authenticated: Returns redirect to login page with return URL
5. After login, user is redirected back to original URL with all parameters preserved

### Cross-Domain Redirect Security

The plugin enhances Indico's Flask-Multipass `validate_next_url()` method to allow redirects to configured trusted domains:

**Configuration Options:**
- `'domain.com'` - Allows only `domain.com` exactly
- `'sub.domain.com'` - Allows only `sub.domain.com` exactly
- `'.domain.com'` - Allows only subdomains (`*.domain.com`), not the bare domain

**Examples** (with `INDICO_CADDY_AUTH_TRUSTED_DOMAINS="fortrancon.org,.example.com,chat.specific.org"`):
- ✅ `https://fortrancon.org` (exact match)
- ✅ `https://api.example.com` (subdomain, due to `.example.com`)
- ✅ `https://chat.specific.org` (exact match)
- ❌ `https://events.fortrancon.org` (blocked, only exact `fortrancon.org` allowed)
- ❌ `https://example.com` (blocked, only `.example.com` configured)
- ❌ `https://malicious.com` (not in trusted list)

**Security:**
- ✅ **Configurable whitelist** - Only specified domains allowed
- ✅ **Flexible patterns** - Support exact domains, subdomains, and wildcards
- ❌ **External domains** blocked by default
- 📝 **Plugin logging** - Shows trusted domains at startup for debugging

This approach works with Indico's standard login flow and provides **maximum flexibility** for administrators.

## Development

### Code Quality

This project uses automated code quality checks:

- **Ruff**: For linting and formatting Python code
- **Pre-commit hooks**: For automatic checks before commits
- **GitHub Actions**: For CI/CD validation

Install development dependencies:
```bash
pip install -r requirements-dev.txt
pre-commit install
```

Run code quality checks locally:
```bash
# Run linter
ruff check .

# Run formatter
ruff format .

# Check syntax
python3 -m py_compile indico_caddy_auth/*.py
```

### GitHub Actions

The repository includes a CI workflow that:
- Runs on push/PR to `main` and `develop` branches
- Executes all pre-commit hooks (ruff linting, formatting, syntax checks, etc.)
- Uses the same configuration as local development

## Testing

Test the endpoint directly:
```bash
# When authenticated
curl -b cookies.txt https://events.fortrancon.org/auth/validate

# When not authenticated (will redirect)
curl -L https://events.fortrancon.org/auth/validate
```
