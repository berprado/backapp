import os
import zipfile
from datetime import datetime
from facturador.database import obtener_evento_abierto, get_cufd_vigente, actualizar_evento_final
from soap_services import verificar_comunicacion, enviar_evento_significativo

def finalizar_evento_si_conectado():
    """
    Verifica si hay un evento activo y finaliza el evento si el sistema ha recuperado la conexión.
    Además, si hay archivos XML offline vinculados, los comprime en un ZIP y lo nombra con el id y código de recepción.
    """
    mensaje, conectado, _ = verificar_comunicacion()
    if not conectado:
        print("[🛑] Aún no hay conexión con el SIN. No se puede finalizar evento.")
        return False

    evento = obtener_evento_abierto()
    if not evento:
        print("[✅] No hay evento abierto. El sistema está en modo normal.")
        return True

    print(f"[📡] Conexión restablecida. Finalizando evento #{evento['id']}...")

    # Paso 1: Obtener CUFD vigente
    cufd_actual = get_cufd_vigente()
    if not cufd_actual:
        print("[⚠️] No se pudo obtener CUFD actual para finalizar el evento.")
        return False

    # Paso 2: Enviar solicitud SOAP al SIN
    fecha_fin = datetime.now()
    codigo_recepcion, transaccion = enviar_evento_significativo(
        evento=evento,
        fecha_fin=fecha_fin,
        cufd=cufd_actual
    )

    if not transaccion:
        print("[❌] El SIN no aceptó el cierre del evento.")
        return False

    # Paso 3: Guardar código de recepción y fecha fin
    actualizar_evento_final(evento_id=evento["id"], fecha_fin=fecha_fin, codigo_recepcion=codigo_recepcion)
    print(f"[✅] Evento #{evento['id']} finalizado exitosamente con código {codigo_recepcion}.")

    # Paso 4: Verificar si hay archivos relacionados
    archivos = [
        f for f in os.listdir("offline")
        if f.startswith(f"offline_{evento['id']}_") and f.endswith(".xml")
    ]

    if archivos:
        os.makedirs("offline_archivos", exist_ok=True)
        nombre_zip = f"offline_archivos/{evento['id']}_{codigo_recepcion}.zip"

        with zipfile.ZipFile(nombre_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for archivo in archivos:
                ruta = os.path.join("offline", archivo)
                zipf.write(ruta, arcname=archivo)

        print(f"[📦] Archivos comprimidos y guardados como: {nombre_zip}")
    else:
        print("[ℹ️] No se encontraron facturas offline para este evento.")

    return True
