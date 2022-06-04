import os

LIBRARY_ROOT = os.path.abspath(os.path.join(os.path.abspath(__file__), os.path.pardir))
MONGODB_HOST = os.environ.get("MONGODB_URL")
