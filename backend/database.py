
from pymongo import MongoClient
from pymongo.errors import PyMongoError

try:
    from .config import settings
except ImportError:
    try:
        from Backend.config import settings
    except ImportError:
        from config import settings



client = MongoClient(
    settings.MONGODB_URI,
    serverSelectionTimeoutMS=3000,
)

database = client[settings.DATABASE_NAME]

candidates_collection = database["candidates"]
jobs_collection = database["jobs"]


def check_database_connection() -> bool:
    """Check whether MongoDB is reachable."""
    try:
        client.admin.command("ping")
        return True
    except PyMongoError:
        return False


def close_database_connection() -> None:
    """Close the MongoDB client."""
    client.close()
