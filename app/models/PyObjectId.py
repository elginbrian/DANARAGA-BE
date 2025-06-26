from typing import Any
from bson import ObjectId
from pydantic.json_schema import JsonSchemaValue
from pydantic_core.core_schema import CoreSchema


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler) -> CoreSchema:
        return handler(source_type, ObjectId)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler
    ) -> JsonSchemaValue:
        return {"type": "string"}

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, values, field=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")