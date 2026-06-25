# schemas.py (Đã sửa)
from pydantic import BaseModel
from datetime import datetime # Thêm import này

# Session
class TrainingSessionCreate(BaseModel):
    num_rounds: int
    lr: float
    local_epochs: int

class TrainingSessionOut(TrainingSessionCreate):
    id: int
    class Config:
        # SỬA lỗi Pydantic V2
        from_attributes = True

# Client submit
class ClientSubmitCreate(BaseModel):
    session_id: int
    client_id: int
    round_number: int
    accuracy: float
    seed: int

class ClientSubmitOut(ClientSubmitCreate):
    id: int
    # SỬA: Dùng datetime để khớp với models.py và cho phép serialize JSON
    timestamp: datetime 
    class Config:
        # SỬA lỗi Pydantic V2
        from_attributes = True

class SessionFindRequest(BaseModel):
    num_rounds: int
    local_epochs: int
    lr: float
    seed: int