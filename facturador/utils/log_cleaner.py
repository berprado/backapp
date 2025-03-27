import os
import glob
import time
from datetime import datetime, timedelta

def clean_xml_responses(max_age_days=7, max_files=1000):
    """
    Limpia archivos antiguos del directorio de respuestas XML
    
    Args:
        max_age_days: Días máximos de antigüedad para mantener archivos
        max_files: Número máximo de archivos a mantener
    
    Returns:
        int: Número de archivos eliminados
    """
    response_dir = "logs/responses"
    if not os.path.exists(response_dir):
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    cutoff_timestamp = cutoff_date.timestamp()
    
    # Obtener todos los archivos XML
    files = glob.glob(f"{response_dir}/*.xml")
    
    # Ordenar por tiempo de modificación (más recientes primero)
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    deleted_count = 0
    
    # Eliminar archivos que excedan el límite de edad o cantidad
    for idx, file in enumerate(files):
        # Conservar verificaciones importantes (no de verificación rutinaria)
        if "verification_response" not in os.path.basename(file) and idx < max_files:
            continue
            
        # Si el archivo es más viejo que el límite o excede la cantidad máxima
        if os.path.getmtime(file) < cutoff_timestamp or idx >= max_files:
            try:
                os.remove(file)
                deleted_count += 1
            except Exception:
                pass
    
    return deleted_count
