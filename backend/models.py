from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base

# Bảng session huấn luyện
class TrainingSession(Base):
    __tablename__ = "training_session"

    id = Column(Integer, primary_key=True, index=True)
    num_rounds = Column(Integer)
    lr = Column(Float)
    local_epochs = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Bảng submit của client
class ClientSubmit(Base):
    __tablename__ = "client_submit"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("training_session.id"))
    client_id = Column(Integer)
    round_number = Column(Integer)
    accuracy = Column(Float)
    seed = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
