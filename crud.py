from typing import List
from sqlalchemy.orm import Session
from models import Comanda


def get_comanda_data(comanda_ids: List[int], db: Session) -> List[dict]:
    comandas_data = db.query(Comanda).filter(Comanda.id_comanda.in_(comanda_ids)).all()
    return [comanda.to_dict() for comanda in comandas_data]