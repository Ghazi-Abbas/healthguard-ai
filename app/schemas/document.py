from pydantic import BaseModel, Field
from datetime import datetime
class DocumentResponse(BaseModel):
    id:int
    authorization_id:int
    filename:str
    content_type:str
    page_count:int
    processing_status:str
    created_at:datetime

    model_config={
        'from_attributes':True
    }
