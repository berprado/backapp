# Sistema de Facturación Digital Refactorizado v1.0

## 📋 Descripción

Sistema de facturación digital refactorizado que cumple con las normativas del SIN (Servicio de Impuestos Nacionales) de Bolivia. Soporte completo para facturación **online** y **offline** con arquitectura modular y mantenible.

## 🏗️ Arquitectura

### Estructura de Directorios

```
facturadorv1/
├── .env                           # Configuración del sistema
├── main.py                        # Punto de entrada principal
├── README.md                      # Esta documentación
├── core/                          # Lógica de negocio central
│   ├── __init__.py
│   ├── rf_connection_detector.py  # Detección automática online/offline
│   ├── rf_business_logic.py       # Lógica de negocio principal
│   ├── rf_offline_manager.py      # Gestión de facturación offline
│   └── rf_invoice_core.py         # Core de procesamiento de facturas
├── services/                      # Servicios externos y comunicación
│   ├── __init__.py
│   ├── rf_siat_client.py          # Cliente para servicios SIAT
│   ├── rf_facturacion_online.py   # Servicio facturación online
│   ├── rf_facturacion_offline.py  # Servicio facturación offline
│   ├── rf_batch_processor.py      # Procesador de lotes
│   └── rf_xml_services.py         # Servicios XML y firma digital
├── operations/                    # Operaciones específicas
│   ├── __init__.py
│   ├── rf_anulacion.py            # Anulación de facturas
│   ├── rf_reversion.py            # Reversión de anulaciones
│   └── rf_estado_factura.py       # Consulta de estados
├── data/                         # Acceso y persistencia de datos
│   ├── __init__.py
│   ├── rf_data_access.py          # Acceso a base de datos
│   ├── rf_models.py               # Modelos de datos
│   └── rf_database.py             # Gestión de conexiones DB
├── ui/                           # Interfaz de usuario
│   ├── __init__.py
│   ├── rf_main_ui.py              # Interfaz principal unificada
│   ├── rf_components.py           # Componentes reutilizables
│   ├── rf_validators.py           # Validadores de UI
│   └── rf_status_indicators.py    # Indicadores de estado
├── utils/                        # Utilidades y helpers
│   ├── __init__.py
│   ├── rf_logger.py               # Logger centralizado
│   ├── rf_xml_utils.py            # Utilidades XML
│   └── rf_file_utils.py           # Helpers de archivos
├── config/                       # Configuración del sistema
│   ├── __init__.py
│   └── rf_settings.py             # ✅ Configuración centralizada
├── resources/                    # Recursos estáticos
│   ├── schemas/                   # ✅ Esquemas XSD
│   │   ├── facturaElectronicaCompraVenta.xsd
│   │   └── SignatureSchema.xsd
│   └── certificates/             # ✅ Certificados y llaves
│       ├── certificado_ok.pem
│       └── private_key_ok.pem
├── storage/                      # Almacenamiento temporal
│   ├── offline_xmls/             # XMLs individuales offline
│   ├── batches/                  # Lotes comprimidos
│   └── .gitkeep
└── logs/                         # Logs del sistema
    └── .gitkeep
```

## ✅ Estado Actual

### Completado
- [x] **Estructura de directorios** - Arquitectura modular definida
- [x] **Configuración centralizada** - Carga desde .env con validaciones
- [x] **Recursos organizados** - XSD y certificados en ubicaciones apropiadas
- [x] **Punto de entrada** - main.py con validación de configuración
- [x] **Documentación base** - README y estructura de archivos

### En Desarrollo
- [ ] **Modelos de datos** (rf_models.py) - Estructuras con validaciones SIN
- [ ] **Logger centralizado** (rf_logger.py) - Sistema de logging unificado
- [ ] **Detector de conexión** (rf_connection_detector.py) - Online/offline automático
- [ ] **Servicios de facturación** - Implementación online y offline
- [ ] **Interfaz unificada** - UI que se adapta al modo detectado

## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.8+
- MySQL/MariaDB
- Streamlit
- Certificado digital válido del SIN

### Configuración
1. Copiar y configurar el archivo `.env` con los datos de tu empresa
2. Colocar certificados en `resources/certificates/`
3. Verificar esquemas XSD en `resources/schemas/`

### Ejecución
```bash
# Desde el directorio facturadorv1
streamlit run main.py
```

## 📐 Principios de Diseño

### Separación de Responsabilidades
- **Core**: Lógica de negocio pura
- **Services**: Comunicación externa (SIAT, DB)
- **UI**: Presentación y interacción
- **Data**: Persistencia y modelos
- **Utils**: Utilidades reutilizables

### Modularidad
- Cada módulo tiene una responsabilidad específica
- Interfaces bien definidas entre módulos
- Facilita testing y mantenimiento

### Compatibilidad
- Reutiliza funciones existentes del sistema actual
- Migración gradual sin romper funcionalidad
- Coexistencia con código legacy usando prefijo `rf_`

## 🔄 Flujo de Facturación

### Modo Online
1. Detección automática de conexión
2. Generación XML modo online (tipo emisión 1)
3. Firma digital XMLDSig
4. Validación contra XSD
5. Compresión Gzip y hash SHA-256
6. Envío inmediato a SIAT
7. Procesamiento de respuesta (908/904)

### Modo Offline
1. Detección de contingencia
2. Registro de evento significativo
3. Generación XML modo offline (tipo emisión 2)
4. Almacenamiento local individual
5. Agrupación en lotes (max 500 facturas)
6. Envío masivo post-contingencia
7. Validación de lotes

## 🔧 Configuración Avanzada

### Variables de Entorno Críticas
```env
# SIAT
API_KEY=TokenApi [tu_token]
CODIGO_SISTEMA=[tu_codigo_sistema]
CUIS=[tu_cuis]
NIT=[tu_nit]

# Base de Datos
DATABASE_URL=mysql+pymysql://user:pass@host:port/db

# Certificados
PRIVATE_KEY_PASSWORD=[contraseña_llave_privada]
```

### Validación de Configuración
El sistema valida automáticamente:
- Presencia de variables críticas
- Existencia de certificados y esquemas
- Conectividad con servicios SIAT
- Estructura de directorios

## 📝 Próximos Desarrollos

1. **rf_models.py** - Modelos con validaciones SIN
2. **rf_logger.py** - Sistema de logging centralizado
3. **rf_connection_detector.py** - Detección automática de modo
4. **rf_facturacion_online.py** - Servicio facturación online
5. **rf_facturacion_offline.py** - Servicio facturación offline
6. **rf_main_ui.py** - Interfaz unificada adaptable

## 🔍 Testing

```bash
# Validar configuración
python -c "from config.rf_settings import validate_settings_on_startup; validate_settings_on_startup()"
```

## 📞 Soporte

Sistema desarrollado según normativas SIN Bolivia para facturación electrónica online y offline.

---

**Versión:** 1.0.0  
**Estado:** En Desarrollo  
**Fecha:** Enero 2025
