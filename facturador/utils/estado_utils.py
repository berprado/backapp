# -*- coding: utf-8 -*-
"""
Utilidades para gestionar transiciones de estado de facturas (anulación y reversión)
con reglas consistentes a nivel de negocio, sin afectar la validación técnica.

- aplicar_anulacion: marca una factura como Anulada y registra motivo/usuario.
- aplicar_reversion: restaura una factura Anulada a Validada (negocio).
- preservar_codigo_recepcion: evita borrar el codigoRecepcion si no hay uno nuevo.

Estas utilidades NO hacen commit por sí mismas: el caller es responsable de
persistir los cambios con la sesión de BD correspondiente.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from database import SessionLocal
from models import FacturaCabecera, SincronizarParametricaMotivoAnulacion
from logger_config import get_logger

logger = get_logger()


def _get_motivo_descripcion(codigo_motivo: Optional[str]) -> Optional[str]:
    """Obtiene la descripción del motivo desde la paramétrica local.

    Args:
        codigo_motivo: Código clasificador seleccionado por el usuario.

    Returns:
        Descripción del motivo o None si no se encuentra.
    """
    if not codigo_motivo:
        return None
    session = SessionLocal()
    try:
        rec = (
            session.query(SincronizarParametricaMotivoAnulacion)
            .filter_by(codigoClasificador=str(codigo_motivo))
            .first()
        )
        return rec.descripcion if rec else None
    finally:
        session.close()


def aplicar_anulacion(
    factura: FacturaCabecera,
    codigo_motivo: Optional[str],
    usuario: str,
) -> None:
    """Aplica reglas de negocio para anulación de factura.

    - estado (negocio) -> "Anulada"
    - estadoValidacion (técnico) -> se mantiene sin cambios
    - fechaAnulacion -> ahora
    - anuladaPor / motivoAnulacion -> poblados
    """
    descripcion = _get_motivo_descripcion(codigo_motivo)
    if not descripcion and codigo_motivo:
        descripcion = f"Motivo {codigo_motivo}"

    factura.estado = "Anulada"
    factura.fechaAnulacion = datetime.now()
    factura.anuladaPor = usuario
    factura.motivoAnulacion = descripcion

    logger.info(
        f"[ESTADO] Factura #{getattr(factura, 'numeroFactura', '?')} → Anulada (motivo={descripcion})"
    )


def aplicar_reversion(
    factura: FacturaCabecera,
    usuario: str,
) -> None:
    """Aplica reglas de negocio para reversión de anulación.

    - estado (negocio) -> "Validada"
    - estadoValidacion (técnico) -> se mantiene sin cambios
    - limpia fechaAnulacion/anuladaPor/motivoAnulacion
    """
    factura.estado = "Validada"
    factura.fechaAnulacion = None
    factura.anuladaPor = None
    factura.motivoAnulacion = None

    logger.info(
        f"[ESTADO] Factura #{getattr(factura, 'numeroFactura', '?')} → Validada (reversión por {usuario})"
    )


def preservar_codigo_recepcion(
    factura: FacturaCabecera,
    nuevo_codigo: Optional[str],
) -> None:
    """Asigna un nuevo código de recepción sólo si es provisto; evita borrar el existente."""
    if nuevo_codigo:
        factura.codigoRecepcion = nuevo_codigo
