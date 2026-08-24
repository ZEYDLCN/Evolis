"""Loaded by pytest before any test module is imported.

Pins DATABASE_URL to a throwaway file *before* src.database.base (and
therefore its module-level engine) gets imported by anything — whichever
test file pytest happens to collect first. Without this, whichever test
module imports src.database.base first wins the default sqlite file for the
whole test session.
"""
import os
import tempfile

_db_dir = tempfile.mkdtemp(prefix="evolis-test-")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_db_dir}/test.db")

# The auth rate limiter (apps/api/rate_limit.py) is a real production
# safeguard, but the test suite legitimately registers many accounts in a
# tight loop from what looks like a single client — disable it here rather
# than in the app itself.
os.environ.setdefault("AUTH_RATE_LIMIT_MAX_REQUESTS", "0")
