
import os

# Use the separate test database whenever pytest runs.
os.environ["DATABASE_NAME"] = "backend_test_db"
