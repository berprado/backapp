import unittest
from unittest.mock import patch, MagicMock
from consulta_punto import create_connection, client, solicitud

class TestConsultaPuntoVenta(unittest.TestCase):

    @patch('mysql.connector.connect')
    def test_create_connection_success(self, mock_connect):
        mock_connect.return_value.is_connected.return_value = True
        connection = create_connection()
        self.assertIsNotNone(connection)
        self.assertTrue(connection.is_connected())

    @patch('mysql.connector.connect')
    def test_create_connection_failure(self, mock_connect):
        mock_connect.side_effect = Exception("Connection failed")
        connection = create_connection()
        self.assertIsNone(connection)

    def test_solicitud_estructura(self):
        expected_keys = {
            "codigoAmbiente",
            "codigoSistema",
            "codigoSucursal",
            "cuis",
            "nit"
        }
        self.assertTrue(expected_keys.issubset(solicitud['SolicitudConsultaPuntoVenta'].keys()))

    @patch('consulta_punto.client.service.consultaPuntoVenta')
    def test_consulta_soap(self, mock_consulta):
        mock_response = {
            'transaccion': True,
            'listaPuntosVentas': [{'codigoPuntoVenta': 1, 'nombre': 'PV1'}]
        }
        mock_consulta.return_value = mock_response
        
        response = client.service.consultaPuntoVenta(**solicitud)
        self.assertTrue(response['transaccion'])
        self.assertEqual(len(response['listaPuntosVentas']), 1)
        self.assertEqual(response['listaPuntosVentas'][0]['codigoPuntoVenta'], 1)

    @patch('consulta_punto.client.service.consultaPuntoVenta')
    def test_consulta_soap_error(self, mock_consulta):
        mock_consulta.side_effect = Exception("SOAP request failed")
        
        with self.assertRaises(Exception) as context:
            client.service.consultaPuntoVenta(**solicitud)
        self.assertTrue("SOAP request failed" in str(context.exception))

if __name__ == '__main__':
    unittest.main()

