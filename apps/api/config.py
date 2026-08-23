import os

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
JWT_ALGORITHM = "HS256"

# Sign in with Google (src/services/auth_service.py::verify_google_credential).
# Create one at https://console.cloud.google.com/apis/credentials — an OAuth
# 2.0 Client ID of type "Web application". Unset = the feature is honestly
# reported as unavailable rather than silently broken (see POST /auth/google).
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
