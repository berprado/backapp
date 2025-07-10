"""
Configuración centralizada para el sistema de facturación refactorizado.
Carga configuraciones desde el archivo .env y proporciona acceso centralizado.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class FacturadorSettings:
    """Gestor centralizado de configuraciones."""
    
    def __init__(self):
        # Cargar variables de entorno desde .env
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)
        
        # Definir rutas base
        self.base_path = Path(__file__).parent.parent
        self.resources_path = self.base_path / 'resources'
        self.storage_path = self.base_path / 'storage'
        self.logs_path = self.base_path / 'logs'
        
        # Cargar configuraciones
        self._load_database_config()
        self._load_siat_config()
        self._load_business_config()
        self._load_paths_config()
    
    def _load_database_config(self):
        """Carga configuración de base de datos."""
        self.database = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'adminerp_copy'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'url': os.getenv('DATABASE_URL', '')
        }
    
    def _load_siat_config(self):
        """Carga configuración del SIAT."""
        self.siat = {
            'wsdl_url': os.getenv('WSDL_URL'),
            'wsdl_url_sync': os.getenv('WSDL_URL_SYNC'),
            'wsdl_url_codigos': os.getenv('WSDL_URL_CODIGOS'),
            'wsdl_url_operaciones': os.getenv('WSDL_URL_OPERACIONES'),
            'wsdl_url_ajuste': os.getenv('WSDL_URL_AJUSTE'),
            'wsdl_url_reversion': os.getenv('WSDL_URL_REVERSION'),
            'wsdl_url_facturacion': os.getenv('WSDL_URL_FACTURACION'),
            'api_key': os.getenv('API_KEY'),
            'codigo_ambiente': int(os.getenv('CODIGO_AMBIENTE', 2)),
            'codigo_punto_venta': int(os.getenv('CODIGO_PUNTO_VENTA', 0)),
            'codigo_empresa': int(os.getenv('CODIGO_EMPRESA', 0)),
            'codigo_sistema': os.getenv('CODIGO_SISTEMA'),
            'codigo_sucursal': int(os.getenv('CODIGO_SUCURSAL', 0)),
            'codigo_modalidad': int(os.getenv('CODIGO_MODALIDAD', 1)),
            'cuis': os.getenv('CUIS'),
            'nit': int(os.getenv('NIT', 0))
        }
    
    def _load_business_config(self):
        """Carga configuración del negocio."""
        self.business = {
            'razon_social': os.getenv('RAZON_SOCIAL', '').strip('"'),
            'departamento': os.getenv('DEPARTAMENTO', '').strip('"'),
            'direccion': os.getenv('DIRECCION', '').strip('"'),
            'municipio': os.getenv('MUNICIPIO', '').strip('"'),
            'nombre_sucursal': os.getenv('NOMBRE_SUCURSAL', '').strip('"'),
            'telefono': os.getenv('TELEFONO', ''),
            'actividad_economica': int(os.getenv('ACTIVIDAD_ECONOMICA', 561110)),
            'codigo_producto_sin': int(os.getenv('CODIGO_PRODUCTO_SIN', 99100)),
            'codigo_documento_sector': int(os.getenv('CODIGO_DOCUMENTO_SECTOR', 1)),
            'codigo_tipo_emision': int(os.getenv('CODIGO_TIPO_EMISION', 1)),
            'codigo_tipo_factura': int(os.getenv('CODIGO_TIPO_FACTURA', 1)),
            'descripcion_tipo_factura': os.getenv('DESCRIPCION_TIPO_FACTURA', '').strip('"'),
            'subtitulo': os.getenv('SUBTITULO', '').strip('"')
        }
    
    def _load_paths_config(self):
        """Carga configuración de rutas."""
        self.paths = {
            'schemas': self.resources_path / 'schemas',
            'certificates': self.resources_path / 'certificates',
            'offline_xmls': self.storage_path / 'offline_xmls',
            'batches': self.storage_path / 'batches',
            'logs': self.logs_path,
            'certificate_file': self.resources_path / 'certificates' / 'certificado_ok.pem',
            'private_key_file': self.resources_path / 'certificates' / 'private_key_ok.pem',
            'xsd_factura': self.resources_path / 'schemas' / 'facturaElectronicaCompraVenta.xsd',
            'xsd_signature': self.resources_path / 'schemas' / 'SignatureSchema.xsd'
        }
    
    def get_private_key_password(self) -> str:
        """Obtiene la contraseña de la llave privada."""
        return os.getenv('PRIVATE_KEY_PASSWORD', '@nali2024')
    
    def is_production_environment(self) -> bool:
        """Verifica si estamos en ambiente de producción."""
        return self.siat['codigo_ambiente'] == 1
    
    def get_full_database_url(self) -> str:
        """Construye la URL completa de la base de datos."""
        if self.database['url']:
            return self.database['url']
        
        return (f"mysql+pymysql://{self.database['user']}:{self.database['password']}"
                f"@{self.database['host']}:{self.database['port']}/{self.database['database']}")
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Valida que todas las configuraciones críticas estén presentes."""
        errors = []
        warnings = []
        
        # Validaciones críticas
        if not self.siat['api_key']:
            errors.append("API_KEY no configurado")
        
        if not self.siat['codigo_sistema']:
            errors.append("CODIGO_SISTEMA no configurado")
        
        if not self.siat['cuis']:
            errors.append("CUIS no configurado")
        
        if not self.siat['nit']:
            errors.append("NIT no configurado")
        
        # Validaciones de archivos
        if not self.paths['certificate_file'].exists():
            errors.append(f"Certificado no encontrado: {self.paths['certificate_file']}")
        
        if not self.paths['private_key_file'].exists():
            errors.append(f"Llave privada no encontrada: {self.paths['private_key_file']}")
        
        if not self.paths['xsd_factura'].exists():
            warnings.append(f"Schema XSD no encontrado: {self.paths['xsd_factura']}")
        
        # Validaciones de conectividad
        if not all([self.siat['wsdl_url'], self.siat['wsdl_url_facturacion']]):
            warnings.append("URLs de WSDL incompletas")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def get_offline_config(self) -> Dict[str, Any]:
        """Obtiene configuración específica para el modo offline."""
        return {
            'max_facturas_por_lote': 500,
            'xml_storage_path': self.paths['offline_xmls'],
            'batches_storage_path': self.paths['batches'],
            'auto_retry_attempts': 3,
            'retry_delay_seconds': 30
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Obtiene configuración para el sistema de logging."""
        return {
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'log_path': self.paths['logs'],
            'max_log_files': int(os.getenv('MAX_LOG_FILES', 30)),
            'log_format': os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
        }

# Instancia global de configuración
settings = FacturadorSettings()

# Función de conveniencia para validar configuración al inicio
def validate_settings_on_startup() -> bool:
    """
    Valida la configuración al iniciar el sistema.
    
    Returns:
        bool: True si la configuración es válida, False si hay errores críticos
    """
    validation_result = settings.validate_configuration()
    
    if not validation_result['valid']:
        print("❌ Errores críticos en la configuración:")
        for error in validation_result['errors']:
            print(f"  - {error}")
        return False
    
    if validation_result['warnings']:
        print("⚠️ Advertencias de configuración:")
        for warning in validation_result['warnings']:
            print(f"  - {warning}")
    
    print("✅ Configuración validada correctamente")
    return True
