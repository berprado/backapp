

---

### **Proceso completo de obtención de comandas y generación de facturas**

El flujo para obtener las comandas y utilizarlas en la generación de facturas se puede dividir en varias etapas. A continuación, detallo cada una de ellas:

---

### **1. Definición del endpoint en main.py**
El archivo main.py define un endpoint en FastAPI que proporciona las comandas. Este endpoint es accesible a través de la URL base configurada en `ENDPOINT_URL` (definida en config.py como `http://127.0.0.1:8000/`).

#### **Ruta `/` en main.py**
```python
@app.get("/", status_code=200, response_model=List[ComandaDetailSchema])
async def get_all_comandas(db: Session = Depends(get_db)):
    comandas = db.query(models.Comanda).all()
    if not comandas:
        raise HTTPException(status_code=404, detail="No se encontraron comandas")
    return comandas
```

- **Propósito**: Este endpoint devuelve todas las comandas almacenadas en la base de datos.
- **Lógica**:
  1. Se utiliza SQLAlchemy para consultar la tabla `comandas` definida en el modelo `Comanda` (`models.py`).
  2. Si no se encuentran comandas, se lanza una excepción HTTP con un código 404.
  3. Si se encuentran comandas, se devuelven como una lista de objetos serializados utilizando el esquema `ComandaDetailSchema`.

- **Estructura de la respuesta**:
  La respuesta tiene la estructura definida en el archivo respuesta.json. Por ejemplo:
  ```json
  [
    {
      "id": 69674,
      "cantidad": 4,
      "id_comanda": 53045,
      "id_producto": null,
      "id_salida_combo_coctel": 50715,
      "id_bar_combo_coctel": "0926",
      "precio_venta": "50.00",
      "sub_total": "200.00",
      "producto_coctel": "72,",
      "id_barra": 1,
      "usuario_reg": "ARNOLD",
      "estado": "HAB",
      "id_operacion": 876,
      "nombre": "V GEBERS MARRAKECH",
      "id_producto_combo": "0926",
      "tipo_salida": 50,
      "estado_comanda": 26,
      "estado_impresion": 31
    }
  ]
  ```

---

### **2. Obtención de comandas desde ui_copy.py**
El archivo ui_copy.py utiliza la función `fetch_comandas` definida en `data_access.py` para obtener las comandas desde el endpoint de FastAPI.

#### **Función `fetch_comandas` en `data_access.py`**
```python
@st.cache_resource
def fetch_comandas():
    try:
        logger.info("Obteniendo comandas")
        response = requests.get(f"{ENDPOINT_URL}")
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al obtener comandas: {e}")
        return [], f"Error al obtener los id_comanda: {e}"
```

- **Propósito**: Realiza una solicitud HTTP GET al endpoint definido en `ENDPOINT_URL` (`http://127.0.0.1:8000/`) para obtener las comandas.
- **Lógica**:
  1. Se registra en el logger que se está intentando obtener las comandas.
  2. Se realiza una solicitud GET al endpoint.
  3. Si la solicitud es exitosa, se devuelve el contenido de la respuesta en formato JSON junto con `None` como mensaje de error.
  4. Si ocurre un error (por ejemplo, problemas de conexión), se registra el error en el logger y se devuelve una lista vacía junto con un mensaje de error.

- **Caché**: La función utiliza el decorador `@st.cache_resource`, lo que significa que los resultados se almacenan en caché para evitar solicitudes repetidas al mismo endpoint.

---

### **3. Filtrado y selección de comandas en ui_copy.py**
Una vez obtenidas las comandas, estas se filtran y se muestran en la interfaz para que el usuario las seleccione.

#### **Filtrado de comandas**
```python
if 'processed_comandas' not in st.session_state:
    st.session_state['processed_comandas'] = set()

id_comanda_set = set(comanda["id_comanda"] for comanda in comandas)
available_comandas = [comanda for comanda in id_comanda_set if comanda not in st.session_state.processed_comandas]
```

- **Propósito**: Excluir las comandas que ya han sido procesadas.
- **Lógica**:
  1. Se utiliza `st.session_state` para mantener un registro de las comandas procesadas.
  2. Se filtran las comandas disponibles (`available_comandas`) excluyendo las que están en `st.session_state['processed_comandas']`.

#### **Selección de comandas**
```python
selected_id_comanda = st.sidebar.multiselect(
    "Selecciona las comandas", 
    available_comandas, 
    key="selected_comandas", 
    placeholder="Comandas Generadas", 
    help="Selecciona las comandas que componen la factura."
)
```

- **Propósito**: Permitir al usuario seleccionar las comandas que desea incluir en la factura.
- **Lógica**:
  1. Se utiliza un `multiselect` de Streamlit para mostrar las comandas disponibles.
  2. Las comandas seleccionadas se almacenan en `selected_id_comanda`.

---

### **4. Generación de la factura**
Una vez que el usuario selecciona las comandas, estas se procesan para generar la factura.

#### **Generación de la factura**
```python
if selected_id_comanda:
    # Procesar las comandas seleccionadas para generar la factura
    # (Lógica específica no incluida en el fragmento proporcionado)
else:
    st.warning("Por favor, selecciona al menos una comanda para generar la factura.")
```

- **Lógica**:
  1. Si el usuario selecciona comandas, estas se procesan para generar la factura.
  2. Si no se seleccionan comandas, se muestra una advertencia en la interfaz.

#### **Generación del PDF**
El archivo ui_copy.py utiliza funciones como `generate_html_invoice` y `html_to_pdf` para generar un PDF de la factura. Estas funciones combinan los datos de las comandas seleccionadas con plantillas HTML para crear un archivo PDF.

---

### **5. Relación con otros servicios**
El archivo .env define configuraciones relacionadas con servicios SOAP (por ejemplo, SIAT). Aunque estos servicios no están directamente relacionados con la obtención de comandas, son utilizados en otras partes del sistema para validar NITs, generar CUFDs, y enviar facturas al sistema tributario.

---

### **Resumen del flujo**
1. **Definición del endpoint**: El endpoint `/` en main.py proporciona las comandas desde la base de datos.
2. **Obtención de comandas**: `fetch_comandas` realiza una solicitud HTTP al endpoint para obtener las comandas.
3. **Filtrado y selección**: Las comandas se filtran y se muestran en la interfaz para que el usuario las seleccione.
4. **Generación de la factura**: Las comandas seleccionadas se procesan para generar la factura, incluyendo la creación de un PDF.
5. **Relación con servicios externos**: Aunque no directamente relacionado con las comandas, el sistema utiliza servicios SOAP para validar y enviar facturas.

