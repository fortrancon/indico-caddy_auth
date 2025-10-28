# Indico Caddy Auth Plugin

This plugin provides an authentication validation endpoint for Caddy's `forward_auth` directive, allowing you to use Indico as an authentication backend for other services.

## Features

- Provides `/auth/validate` endpoint for Caddy forward_auth
- Handles authentication redirects with proper return URLs
- Integrates seamlessly with Indico's session management
- Returns `Remote-User` header for authenticated users

## Installation

1. Install the plugin:
```bash
cd caddy_auth
pip install -e .
```

2. Enable the plugin in your `indico.conf`:
```python
PLUGINS = {'caddy_auth'}

# Configure session cookies for cross-subdomain use
SESSION_COOKIE_DOMAIN = '.fortrancon.org'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
```

3. Restart Indico

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
    }
    reverse_proxy localhost:9991
}
```

## How It Works

1. User visits `chat.fortrancon.org`
2. Caddy calls `localhost:8080/auth/validate`
3. If user is authenticated: Returns 200 with `Remote-User` header
4. If user is not authenticated: Returns redirect to login page with return URL
5. After login, user is redirected back to original URL

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
