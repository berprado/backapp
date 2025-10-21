"""
Script de Diagnóstico y Corrección de Factura #777
==================================================

PROPÓSITO:
----------
1. Verificar el estado REAL de la factura #777 en el SIAT
2. Comparar con el estado en la base de datos local
3. Detectar inconsistencias en las columnas de estado
4. Proponer corrección si es necesario

CONTEXTO:
---------
Factura #777 presenta inconsistencia:
- estado: "Anulada"
- estadoValidacion: "VALIDA" ← Inconsistente
- resultadoValidacion: "VALIDADA" ← Inconsistente

AUTOR: Sistema de Facturación Electrónica
FECHA: 16 de octubre de 2025
"""

import sys
import os

# Añadir el directorio padre al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import FacturaCabecera
from estado_factura import verificar_estado_factura
from datetime import datetime

def print_header(title):
    """Imprime un encabezado formateado"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_section(title):
    """Imprime un título de sección"""
    print(f"\n{title}")
    print("-" * 70)

def diagnosticar_factura_777():
    """
    Diagnóstico completo de la factura #777
    """
    print_header("DIAGNOSTICO DE FACTURA #777")
    print(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ========================================================================
    # PASO 1: Consultar estado en Base de Datos Local
    # ========================================================================
    print_section("PASO 1: Estado en Base de Datos Local")
    
    session = SessionLocal()
    try:
        factura = session.query(FacturaCabecera).filter_by(numeroFactura=777).first()
        
        if not factura:
            print("❌ ERROR: Factura #777 no encontrada en la base de datos")
            return
        
        print(f"✅ Factura #777 encontrada")
        print(f"\n📊 Datos actuales:")
        print(f"   numeroFactura:        {factura.numeroFactura}")
        print(f"   cuf:                  {factura.cuf[:30]}...")
        print(f"   codigoRecepcion:      {factura.codigoRecepcion or 'NULL'}")
        print(f"   fechaEmision:         {factura.fechaEmision}")
        print(f"   montoTotal:           {factura.montoTotal} Bs.")
        
        print(f"\n🔍 Columnas de Estado:")
        print(f"   estado:               {factura.estado}")
        print(f"   estadoValidacion:     {factura.estadoValidacion}")
        print(f"   resultadoValidacion:  {factura.resultadoValidacion}")
        
        print(f"\n📅 Información de Anulación:")
        print(f"   fechaAnulacion:       {factura.fechaAnulacion or 'NULL'}")
        print(f"   anuladoPor:           {factura.anuladoPor or 'NULL'}")
        print(f"   motivoAnulacion:      {factura.motivoAnulacion or 'NULL'}")
        
        # Detectar inconsistencias en BD local
        inconsistencias_locales = []
        
        if factura.estado == "Anulada":
            if factura.estadoValidacion != "ANULADA":
                inconsistencias_locales.append(
                    f"estadoValidacion='{factura.estadoValidacion}' (debería ser 'ANULADA')"
                )
            if not factura.fechaAnulacion:
                inconsistencias_locales.append(
                    "fechaAnulacion es NULL (debería tener fecha)"
                )
        
        if inconsistencias_locales:
            print(f"\n⚠️  INCONSISTENCIAS DETECTADAS EN BD LOCAL:")
            for i, inc in enumerate(inconsistencias_locales, 1):
                print(f"   {i}. {inc}")
        else:
            print(f"\n✅ Estado local consistente")
        
        # Guardar datos para comparar después
        estado_bd_local = {
            'estado': factura.estado,
            'estadoValidacion': factura.estadoValidacion,
            'resultadoValidacion': factura.resultadoValidacion,
            'codigoRecepcion': factura.codigoRecepcion,
            'fechaAnulacion': factura.fechaAnulacion
        }
        
    except Exception as e:
        print(f"❌ ERROR al consultar BD local: {e}")
        return
    finally:
        session.close()
    
    # ========================================================================
    # PASO 2: Verificar estado en SIAT (forzando consulta en tiempo real)
    # ========================================================================
    print_section("PASO 2: Estado en SIAT (Servicio de Impuestos Nacionales)")
    
    print("🔄 Consultando estado en el SIAT (force_check=True)...")
    
    try:
        resultado = verificar_estado_factura("777", force_check=True)
        
        print(f"\n📡 Respuesta del SIAT:")
        print(f"   Estado:               {resultado.get('estado_siat', 'N/A')}")
        print(f"   Código estado:        {resultado.get('codigo_estado_siat', 'N/A')}")
        print(f"   Transacción:          {resultado.get('transaccion', 'N/A')}")
        print(f"   Mensaje:              {resultado.get('mensaje', 'N/A')[:100]}...")
        
        # Mapear código de estado SIAT a descripción
        codigo_siat = resultado.get('codigo_estado_siat', '')
        mapeo_estados = {
            '690': 'FACTURA VÁLIDA (activa)',
            '691': 'FACTURA ANULADA',
            '902': 'FACTURA NO ENCONTRADA EN SIAT',
            '986': 'FACTURA EN PROCESO DE VALIDACIÓN'
        }
        descripcion_estado = mapeo_estados.get(codigo_siat, f'Código desconocido: {codigo_siat}')
        print(f"   Descripción:          {descripcion_estado}")
        
        estado_siat = resultado.get('estado_siat', '').upper()
        
    except Exception as e:
        print(f"❌ ERROR al consultar SIAT: {e}")
        print("   No se puede continuar con el diagnóstico.")
        return
    
    # ========================================================================
    # PASO 3: Comparar Estados (BD Local vs SIAT)
    # ========================================================================
    print_section("PASO 3: Comparación BD Local vs SIAT")
    
    # Normalizar estados para comparación
    estado_bd = estado_bd_local['estado'].upper() if estado_bd_local['estado'] else ''
    
    print(f"\n📊 Comparación:")
    print(f"   BD Local (estado):    {estado_bd}")
    print(f"   SIAT (estado):        {estado_siat}")
    
    if estado_bd == estado_siat:
        print(f"\n✅ ESTADOS COINCIDEN")
        print(f"   La columna 'estado' está sincronizada con el SIAT")
    else:
        print(f"\n❌ INCONSISTENCIA CRÍTICA DETECTADA")
        print(f"   BD Local dice: {estado_bd}")
        print(f"   SIAT dice:     {estado_siat}")
    
    # ========================================================================
    # PASO 4: Análisis y Diagnóstico
    # ========================================================================
    print_section("PASO 4: Análisis y Diagnóstico")
    
    if estado_siat == "VÁLIDA" and estado_bd == "ANULADA":
        print("\n🔴 PROBLEMA IDENTIFICADO:")
        print("   La factura está marcada como ANULADA localmente,")
        print("   pero el SIAT la tiene como VÁLIDA.")
        print("\n📋 Posibles causas:")
        print("   1. La anulación falló al enviarse al SIAT")
        print("   2. La anulación fue rechazada pero la BD se actualizó igual")
        print("   3. La factura fue REVERTIDA exitosamente (anulación deshecha)")
        print("\n💡 Acción recomendada:")
        print("   - Si la factura DEBE estar anulada:")
        print("     → Anular nuevamente usando la interfaz del sistema")
        print("   - Si la factura está correcta en el SIAT:")
        print("     → Ejecutar corrección automática (ver PASO 5)")
    
    elif estado_siat == "ANULADA" and estado_bd == "ANULADA":
        print("\n✅ ESTADO CORRECTO:")
        print("   La factura está anulada tanto en BD local como en SIAT")
        
        # Pero verificar las otras columnas
        if estado_bd_local['estadoValidacion'] != "ANULADA":
            print("\n⚠️  Sin embargo, las columnas complementarias tienen inconsistencias:")
            print(f"   estadoValidacion: {estado_bd_local['estadoValidacion']} (debería ser 'ANULADA')")
            print(f"   resultadoValidacion: {estado_bd_local['resultadoValidacion']}")
            print("\n💡 Acción recomendada:")
            print("   → Ejecutar corrección de columnas complementarias (ver PASO 5)")
    
    elif estado_siat == "VÁLIDA" and estado_bd == "VALIDA":
        print("\n✅ FACTURA VÁLIDA Y ACTIVA:")
        print("   La factura está válida tanto en BD local como en SIAT")
        print("\n⚠️  Si intentó revertir una anulación:")
        print("   - La reversión fue EXITOSA")
        print("   - La factura volvió a estado VÁLIDO")
        print("   - NO puede revertirse nuevamente (solo 1 reversión permitida)")
    
    elif estado_siat == "ANULADA" and estado_bd == "VALIDA":
        print("\n🔴 PROBLEMA IDENTIFICADO:")
        print("   La factura está marcada como VÁLIDA localmente,")
        print("   pero el SIAT la tiene como ANULADA.")
        print("\n💡 Acción recomendada:")
        print("   → Ejecutar corrección automática (ver PASO 5)")
    
    # ========================================================================
    # PASO 5: Propuesta de Corrección
    # ========================================================================
    print_section("PASO 5: Propuesta de Corrección Automática")
    
    if estado_siat != estado_bd or inconsistencias_locales:
        print("\n🔧 SE REQUIERE CORRECCIÓN")
        print("\n📝 Acciones propuestas:")
        
        session = SessionLocal()
        try:
            factura = session.query(FacturaCabecera).filter_by(numeroFactura=777).first()
            
            print(f"\n   UPDATE factura_cabecera SET")
            
            if estado_siat == "VÁLIDA":
                print(f"      estado = 'Valida',")
                print(f"      estadoValidacion = 'VALIDADA',")
                print(f"      resultadoValidacion = '690 - FACTURA VALIDA',")
                print(f"      fechaAnulacion = NULL,")
                print(f"      anuladoPor = NULL,")
                print(f"      motivoAnulacion = NULL")
            elif estado_siat == "ANULADA":
                print(f"      estado = 'Anulada',")
                print(f"      estadoValidacion = 'ANULADA',")
                print(f"      resultadoValidacion = '691 - FACTURA ANULADA'")
                if not estado_bd_local['fechaAnulacion']:
                    print(f"      fechaAnulacion = CURRENT_TIMESTAMP")
            
            print(f"   WHERE numeroFactura = 777;")
            
            print("\n❓ ¿Desea aplicar esta corrección? (s/n): ", end='')
            respuesta = input().strip().lower()
            
            if respuesta == 's':
                print("\n🔄 Aplicando corrección...")
                
                if estado_siat == "VÁLIDA":
                    factura.estado = "Valida"
                    factura.estadoValidacion = "VALIDADA"
                    factura.resultadoValidacion = "690 - FACTURA VALIDA"
                    factura.fechaAnulacion = None
                    factura.anuladoPor = None
                    factura.motivoAnulacion = None
                elif estado_siat == "ANULADA":
                    factura.estado = "Anulada"
                    factura.estadoValidacion = "ANULADA"
                    factura.resultadoValidacion = "691 - FACTURA ANULADA"
                    if not factura.fechaAnulacion:
                        factura.fechaAnulacion = datetime.now()
                
                session.commit()
                print("✅ Corrección aplicada exitosamente")
                
                # Verificar resultado
                print("\n🔍 Verificando corrección...")
                session.refresh(factura)
                print(f"   estado:              {factura.estado}")
                print(f"   estadoValidacion:    {factura.estadoValidacion}")
                print(f"   resultadoValidacion: {factura.resultadoValidacion}")
                
            else:
                print("\n❌ Corrección cancelada por el usuario")
                
        except Exception as e:
            print(f"\n❌ ERROR al aplicar corrección: {e}")
            session.rollback()
        finally:
            session.close()
    else:
        print("\n✅ NO SE REQUIERE CORRECCIÓN")
        print("   Todos los estados están sincronizados correctamente")
    
    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================
    print_section("RESUMEN DEL DIAGNÓSTICO")
    
    print(f"\n✅ Factura:              #777")
    print(f"✅ CUF:                  {factura.cuf[:30]}...")
    print(f"✅ Código Recepción:     {estado_bd_local['codigoRecepcion'] or 'NULL'}")
    print(f"\n📊 Estado Final:")
    print(f"   BD Local:             {estado_bd}")
    print(f"   SIAT:                 {estado_siat}")
    print(f"   ¿Sincronizado?:       {'✅ SÍ' if estado_bd == estado_siat else '❌ NO'}")
    
    print("\n" + "=" * 70)
    print("  FIN DEL DIAGNÓSTICO")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        diagnosticar_factura_777()
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnóstico interrumpido por el usuario")
    except Exception as e:
        print(f"\n\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
