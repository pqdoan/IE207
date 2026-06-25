from sqlalchemy.orm import Session
import models, schemas

# --------- Session ---------
def create_session(db: Session, session: schemas.TrainingSessionCreate):
    db_item = models.TrainingSession(**session.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_sessions(db: Session):
    return db.query(models.TrainingSession).all()


# --------- ClientSubmit ---------
def create_submit(db: Session, submit: schemas.ClientSubmitCreate):
    """
    Lưu dữ liệu submit của client vào DB
    """
    db_item = models.ClientSubmit(**submit.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_submits_by_client(db: Session, client_id: int, session_id: int = None):
    """
    Lấy tất cả submit của client_id, có thể lọc theo session_id
    """
    query = db.query(models.ClientSubmit).filter(models.ClientSubmit.client_id == client_id)
    if session_id:
        query = query.filter(models.ClientSubmit.session_id == session_id)
    return query.order_by(models.ClientSubmit.round_number).all()

LR_TOLERANCE = 1e-6

def find_sessions_by_params(db: Session, num_rounds: int, local_epochs: int, lr: float, seed: int):
    lr_min = lr - LR_TOLERANCE
    lr_max = lr + LR_TOLERANCE
    
    query = (
        db.query(models.TrainingSession)
        .join(models.ClientSubmit, models.TrainingSession.id == models.ClientSubmit.session_id)
        .filter(models.TrainingSession.num_rounds == num_rounds)
        .filter(models.TrainingSession.local_epochs == local_epochs)
        .filter(models.TrainingSession.lr.between(lr_min, lr_max)) # LỌC GẦN ĐÚNG
        .filter(models.ClientSubmit.seed == seed)
        .group_by(models.TrainingSession.id)
    )
    return query.all()

def get_submits_by_session(db: Session, session_id: int):
    """
    Lấy tất cả submit của tất cả client thuộc một session_id cụ thể,
    sắp xếp theo client_id và round_number
    """
    return (
        db.query(models.ClientSubmit)
        .filter(models.ClientSubmit.session_id == session_id)
        .order_by(models.ClientSubmit.client_id, models.ClientSubmit.round_number)
        .all()
    )

def count_and_last_submit(db: Session, client_id: int):
    # Tổng số submit
    count = (
        db.query(models.ClientSubmit)
        .filter(models.ClientSubmit.client_id == client_id)
        .count()
    )

    # Submit cuối cùng
    last = (
        db.query(models.ClientSubmit)
        .filter(models.ClientSubmit.client_id == client_id)
        .order_by(models.ClientSubmit.timestamp.desc())
        .first()
    )

    return count, last
