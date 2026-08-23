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
