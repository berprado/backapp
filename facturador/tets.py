import xml.etree.ElementTree as ET
import os
import streamlit as st

def parse_xml_and_save(factura_numero, xml_dir="xmls"):
    """
    Parsea un archivo XML de factura y guarda la información en un archivo de texto.

    Args:
        factura_numero: El número de factura a buscar.
        xml_dir: El directorio donde se encuentran los archivos XML.
    """

    matching_files = [
        filename for filename in os.listdir(xml_dir)
        if filename.startswith(f"factura_{factura_numero}_") and filename.endswith(".xml")
    ]

    if not matching_files:
        st.error(f"No se encontró ningún archivo XML para la factura {factura_numero}.")
        return

    xml_file = os.path.join(xml_dir, matching_files[0])  # Toma el primer archivo coincidente

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        cabecera_data = {}
        detalle_data = []

        for cabecera_element in root.find("cabecera"):
            cabecera_data[cabecera_element.tag] = cabecera_element.text

        for detalle_element in root.findall("detalle"):
             detalle_item = {}
             for element in detalle_element:
                 detalle_item[element.tag] = element.text
             detalle_data.append(detalle_item)


        output_filename = f"factura_{factura_numero}_.txt"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("Cabecera:\n")
            for key, value in cabecera_data.items():
                f.write(f"{key}: {value}\n")

            f.write("\nDetalle:\n")
            for item in detalle_data:
                for key, value in item.items():
                     f.write(f"  {key}: {value}\n")
                f.write("\n")  # Separador entre items de detalle


        st.success(f"Información de la factura {factura_numero} guardada en {output_filename}")
        with open(output_filename, 'r', encoding='utf-8') as f:
            file_contents = f.read()
            st.text_area("Contenido del archivo de texto:", value=file_contents, height=400)


    except ET.ParseError as e:
        st.error(f"Error al parsear el archivo XML: {e}")
    except Exception as e:
        st.error(f"Ocurrió un error: {e}")


# Interfaz Streamlit
st.title("Parser de Facturas XML")

factura_numero = st.text_input("Ingrese el número de factura:", "")

if st.button("Procesar"):
    if factura_numero:
       parse_xml_and_save(factura_numero)
    else:
        st.warning("Por favor, ingrese un número de factura.")