import os
from dotenv import load_dotenv

# .env file ko load karne ke liye
load_dotenv()

# Ab yeh sahi tarike se aapki .env file se real values uthayega
MONGODB_URL_KEY = os.getenv("MONGODB_URL_KEY")
MONGODB_DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME")

SESSION_PRODUCT_KEY: str = "product_name"