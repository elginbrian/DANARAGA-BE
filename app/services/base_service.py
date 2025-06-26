from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import Any, Dict, List, Optional, Union
from app.utils.serialization import serialize_mongo_document, serialize_mongo_list, prepare_mongo_id

class BaseService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db