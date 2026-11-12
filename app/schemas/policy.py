from datetime import datetime

from pydantic import BaseModel

class PolicyCreater(BaseModel):
    name:str
    version:str
    description:str | None =None

class PolicyResponse(BaseModel):
    id:int
    name:str
    version:str
    description:str |None
    created_at:datetime
    model_config={
        "from_attributes":True
    }

class PolicyDocumentResponse(BaseModel):
    id:int
    policy_id:int
    filename:str
    content_type:str
    processing_status:str
    indexing_status: str
    page_count:int
    created_at: datetime

    model_config={
        "from_attributes":True
    }
