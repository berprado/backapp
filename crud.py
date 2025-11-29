from typing import List
from sqlalchemy.orm import Session
from models_api import Comanda  # Importamos desde models_api en lugar de models

def get_comanda_data(comanda_ids: List[int], db: Session) -> List[Comanda]:
    """
    Obtiene datos de comandas por sus IDs
    
    Args:
        comanda_ids: Lista de IDs de comandas
        db: Sesión de base de datos
        
    Returns:
        Lista de comandas
    """
    comandas_data = db.query(Comanda).filter(
        Comanda.id_comanda.in_(comanda_ids),
        Comanda.sub_total != 0
    ).all()
    return comandas_data
