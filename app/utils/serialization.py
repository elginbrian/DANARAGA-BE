from bson import ObjectId
from typing import Any, Dict, List, Union
from datetime import datetime

def serialize_mongo_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
   
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, dict):
            doc[key] = serialize_mongo_document(value)
        elif isinstance(value, list):
            doc[key] = [serialize_mongo_document(item) if isinstance(item, dict) else 
                       (str(item) if isinstance(item, ObjectId) else item) for item in value]
    
    return doc

def serialize_mongo_list(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [serialize_mongo_document(doc) for doc in docs]

def prepare_mongo_id(doc_id: Union[str, ObjectId]) -> ObjectId:
    if isinstance(doc_id, str):
        return ObjectId(doc_id)
    return doc_id