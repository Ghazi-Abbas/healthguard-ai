from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuthorizationWorkflowResponse(BaseModel):
    id: int
    authorization_id: int
    organization_id: int
    thread_id: str
    workflow_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
