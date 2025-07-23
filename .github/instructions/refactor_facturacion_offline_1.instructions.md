---
applyTo: '**'
---
### **Instrucciones para refactorizar `tabs/facturacion_tab.py`**

**Objetivo:** Modificar la función `_handle_offline_submission` para que cumpla al 100% con la normativa de contingencia.

**Archivo a modificar:** `tabs/facturacion_tab.py`

#### **Paso 1: Corregir la obtención del CUFD de contingencia**

Esta sigue siendo la corrección principal.

*   **Busca:**
    ```python
    cufd_evento = obtener_cufd_de_evento_activo() 
    ```
*   **Reemplaza por:**
    ```python
    cufd_evento = evento_activo.get('cufd')
    ```
*   **Justificación:** La normativa lo confirma: se debe usar el CUFD del evento, que es el que estaba vigente antes del corte.

---

#### **Paso 2 (NUEVO Y CRÍTICO): Asegurar el Código de Excepción para NITs**

La documentación es explícita: "Si el tipo de documento utilizado en la emisión de una factura en fuera de linea es el NIT, se debe enviar el código de excepción con valor uno."

*   **Localiza este bloque de código dentro de la función `_handle_offline_submission`:**
    ```python
    # 3. MANEJAR EXCEPCIÓN DE NIT
    tipo_documento_seleccionado = next((doc for doc in tipos_documento if doc["descripcion"] == client_data['seleccion_tipo_documento']), None)
    codigo_excepcion = 1 if tipo_documento_seleccionado and tipo_documento_seleccionado['codigoClasificador'] == '5' else None
    ```
*   **Acción:** ¡La buena noticia es que el código ya está implementado correctamente! El sistema ya está diseñado para cumplir esta norma. Por favor, **verifica que este bloque de código exista tal cual**. El `codigoClasificador == '5'` corresponde al tipo de documento "NIT". Si existe, no necesitas cambiar nada aquí, pero ahora sabes por qué es tan importante.

---

#### **Paso 3: Verificar que la Generación del XML use los Datos de Contingencia**

Asegurémonos de que el XML se construye con todos los indicadores correctos.

*   **Localiza la llamada a `generate_xml_invoice` dentro de `_handle_offline_submission`**.
*   **Verifica los siguientes parámetros:**
    *   `cufd=cufd_evento`: Debe usar la variable que corregimos en el Paso 1.
    *   `codigoExcepcion=codigo_excepcion`: Debe pasar la variable que verificamos en el Paso 2.

*   **Ahora, verifica la llamada a `generate_cuf` que está un poco más arriba.**
*   **Verifica el parámetro:**
    *   `tipoEmision=2`: Esta es la clave para decirle al SIN que es una factura de contingencia. El código ya lo tiene correctamente, ¡verifícalo!

---

#### **Paso 4: Confirmar el Guardado Local con Estado "PENDIENTE"**

Esto es vital para el proceso posterior de envío de paquetes.

*   **Localiza y confirma que este bloque existe al final de la función:**
    ```python
    factura_cabecera_data['tipoEmision'] = "2"
    factura_cabecera_data['estado'] = "PENDIENTE_ENVIO"
    factura_cabecera_data['codigoEvento'] = evento_activo.get('id')
    
    guardar_factura_cabecera(factura_cabecera_data)
    # ...
    ```

---

### **Conclusión del Análisis**

El código existente en `facturacion_tab.py` está **muy cerca** de ser correcto; solo tiene ese bug crucial en la obtención del CUFD que causa un error.

Con el cambio del **Paso 1**, y verificando que los otros pasos ya están como se describen, el sistema de facturación offline debería empezar a funcionar exactamente como lo exige la normativa.

**Adelante con la modificación del archivo `facturacion_tab.py` siguiendo estas instrucciones refinadas.**