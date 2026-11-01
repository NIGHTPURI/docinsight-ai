import os
os.environ["OPENAI_API_KEY"] = ""
os.environ["DATABASE_URL"] = "sqlite://"

from app.config import settings
