# Indico Caddy Auth Plugin

This plugin provides an authentication validation endpoint for Caddy's `forward_auth` directive, allowing you to use Indico as an authentication backend for other services.

## Features

- Provides `/auth/validate` endpoint for Caddy forward_auth
- Handles authentication redirects with proper return URLs
- Integrates seamlessly with Indico's session management
- Returns `Remote-User` header for authenticated users
- **Monkeypatches Flask-Multipass** to allow cross-subdomain redirects for configured trusted domains
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
export INDICO_CADDY_AUTH_TRUSTED_DOMAINS="fortrancon.org,chat.example.com,.trusted.org"

# Configure session cookie domain for cross-subdomain use (optional)
export INDICO_CADDY_AUTH_SESSION_COOKIE_DOMAIN_OVERRIDE=".fortrancon.org"
```

**Domain Configuration Examples:**
- `fortrancon.org` - Allows only fortrancon.org exactly
- `chat.example.com` - Allows only chat.example.com exactly
- `.trusted.org` - Allows *.trusted.org (note the leading dot)

4. Restart Indico

## Usage with Caddy

Configure Caddy to use the auth endpoint:

```caddyfile
events.fortrancon.org {
    reverse_proxy localhost:8080
}

chat.fortrancon.org {
    forward_auth localhost:8080 {
        uri /auth/validate
        copy_headers Remote-User
        header_up Host events.fortrancon.org
    }
    reverse_proxy localhost:9991
}
```

**Important Notes**:
- Use `localhost:8080` (direct backend) for `forward_auth` to avoid Caddy loops
- The `header_up Host events.fortrancon.org` line ensures Indico accepts the auth request
- Query parameters from the original request are preserved in redirect URLs

## How It Works

1. User visits `chat.fortrancon.org`
2. Caddy calls `localhost:8080/auth/validate`
3. If user is authenticated: Returns 200 with `Remote-User` header
4. If user is not authenticated: Returns redirect to login page with return URL
5. **Plugin monkeypatches Flask-Multipass** to allow redirects to configured trusted domains
6. After login, user is redirected back to original URL with all parameters preserved

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
