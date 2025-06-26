from fastapi.encoders import jsonable_encoder
from bson import ObjectId
from typing import Any, Dict, List

class MongoJSONEncoder:
    
    @staticmethod
    def encode_document(document: Dict[str, Any]) -> Dict[str, Any]:
        if not document:
            return document
        
        if "_id" in document:
            if isinstance(document["_id"], ObjectId):
                document["_id"] = str(document["_id"])
        
        return jsonable_encoder(document)
    
    @staticmethod
    def encode_list(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [MongoJSONEncoder.encode_document(doc) for doc in documents]