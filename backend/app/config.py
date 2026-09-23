"""Central configuration, loaded from environment variables."""
import os

from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "queueflow")

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me-before-deploying-to-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "43200"))  # 30 days
