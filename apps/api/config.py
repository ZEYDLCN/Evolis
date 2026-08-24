import os

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # "development" | "production"

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
JWT_ALGORITHM = "HS256"

# CORS: comma-separated list of allowed origins, e.g.
# "https://app.evolis.example,https://evolis.example". No env var set = the
# permissive local-dev default (both Next.js dev ports); ENVIRONMENT=production
# with this unset is refused at startup rather than silently falling back to
# "*" (see apps/api/main.py).
# Auth brute-force guard (apps/api/rate_limit.py). Set the max to 0 to
# disable entirely — used by the test suite, which legitimately registers
# many accounts in a tight loop from a single client.
AUTH_RATE_LIMIT_MAX_REQUESTS = int(os.getenv("AUTH_RATE_LIMIT_MAX_REQUESTS", "10"))
AUTH_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60"))

_cors_env = os.getenv("CORS_ALLOWED_ORIGINS")
CORS_EXPLICITLY_SET = bool(_cors_env)
CORS_ALLOWED_ORIGINS = (
    [origin.strip() for origin in _cors_env.split(",") if origin.strip()]
    if _cors_env
    else ["http://localhost:3000", "http://127.0.0.1:3000"]
)

# Sign in with Google (src/services/auth_service.py::verify_google_credential).
# Create one at https://console.cloud.google.com/apis/credentials — an OAuth
# 2.0 Client ID of type "Web application". Unset = the feature is honestly
# reported as unavailable rather than silently broken (see POST /auth/google).
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
