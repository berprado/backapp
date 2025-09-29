# Eventos Significativos Pendientes

## Resumen rapido
- Este documento registra los eventos significativos del SIN que aun no cuentan con flujo end to end dentro de la aplicacion.
- El objetivo es reutilizar las piezas ya implementadas (registro local, cierre automatico, empaquetado) para minimizar nuevo codigo.

## Eventos sin flujo activo
| Codigo | Descripcion oficial | Estado actual en el sistema | Impacto operativo |
|--------|---------------------|-----------------------------|-------------------|
| 6 | Cambio de infraestructura del sistema o falla de hardware | No se crea evento automaticamente ni se ofrece inicio manual | Contingencia prolongada cuando el problema es de hardware, el sistema termina registrando evento tipo 5 por defecto |
| 7 | Corte de suministro de energia electrica | No se crea evento automaticamente ni se ofrece inicio manual | Facturacion manual sin asociarla al codigo correcto, posibles observaciones al enviar paquetes |

## Componentes listos para reutilizar
- `facturador/data_access.py:197` ya garantiza un unico evento abierto, carga descripcion desde la tabla parametrica y vincula el CUFD vigente.
- `facturador/contingencia_auto.py:13` cierra eventos y dispara el envio de paquetes reutilizando `finalizar_evento_si_conectado()` para cualquier codigo.
- `facturador/pages/2_Eventos_Significativos.py:78` expone el formulario para eventos planificados (codigos 3 y 4) reutilizable como molde para agregar opciones adicionales.
- `facturador/communication_manager.py:41` contiene la enumeracion completa de codigos 1-7 y orquesta la deteccion primaria.
- `facturador/contingency_packager.py:409` registra eventos ante el SIN pero hoy envia siempre `codigoEvento = 1`, lo que debe generalizarse.

## Plan de implementacion
1. **Extender la deteccion**
   - Ajustar `soap_services.verificar_comunicacion()` y `communication_manager` para mapear errores que indiquen hardware o energia (p. ej. heuristicas de ping a dispositivos locales, chequeo de UPS, flags manuales).
   - Permitir que el diagnostico de `communication_manager` exponga en la UI el selector manual cuando el origen es interno (hardware/energia) y no puede diagnosticarse automaticamente.
2. **Registrar eventos 6/7 desde la UI**
   - Duplicar el formulario de `2_Eventos_Significativos.py` en una nueva seccion, habilitando codigos 6 y 7 cuando el sistema entre en contingencia no planificada.
   - Reutilizar `registrar_evento_local_normativo()` para guardar el evento y vincular el CUFD sin crear funciones nuevas.
   - Mostrar etiquetas y mensajes especificos segun `TipoContingencia` en `main.py` para guiar al usuario.
3. **Usar el codigo correcto en empaquetado**
   - Modificar `ContingencyPackager.register_significant_event()` para recibir el codigo del evento activo (obtenido via `obtener_evento_activo_actual()`) en lugar de enviar el valor fijo `1`.
   - Propagar el `codigo_evento` a `send_package_multiple_invoices()` y al resto del pipeline para que el SIN reciba la clasificacion correcta.
4. **Validacion y cierre**
   - Cubrir con pruebas manuales: crear evento 6 y 7, emitir facturas offline, cerrar con `finalizar_evento_si_conectado()` y verificar que el paquete usa el codigo correcto.
   - Documentar el flujo en `docs/README_OFFLINE.md` o documento equivalente una vez completado.

## Riesgos y pendientes
- Determinar heuristicas confiables para distinguir codigos 5, 6 y 7 requiere definiciones operativas (quien reporta la causa, sensores disponibles, etc.).
- La version actual de `contingency_manager` esta parcialmente deprecada; evaluar si conviene reactivarla para soportar monitoreo fisico o implementar un panel ligero en Streamlit.
- Cualquier cambio en empaquetado debe sincronizarse con QA para validar en el ambiente piloto del SIN.
