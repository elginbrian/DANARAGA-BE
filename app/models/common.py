from pydantic import BaseModel, Field
from typing import Optional

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, *args, **kwargs):
        if not isinstance(v, str) or not len(v) == 24: # Contoh validasi sederhana
             # raise TypeError('Invalid ObjectId') # Anda bisa menambahkan validasi yang lebih ketat jika perlu
             pass
        return str(v)

class IDModelMixin(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)