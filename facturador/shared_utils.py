"""
Funciones utilitarias que pueden ser usadas por cualquier módulo del sistema.
Este archivo centraliza funciones comunes para evitar duplicación de código.
"""
from num2words import num2words

def numero_a_palabras_con_decimales_como_fraccion(numero, lang='es'):
    """
    Convierte un número a palabras con decimales como fracción.
    
    Args:
        numero (float): Número a convertir
        lang (str): Idioma para la conversión (por defecto 'es')
    
    Returns:
        str: Número en palabras con formato "X Y/100 bolivianos"
    """
    if not numero:
        return ""
    
    parte_entera = int(numero)
    parte_decimal = int(round((numero - parte_entera) * 100))
    parte_entera_palabras = num2words(parte_entera, lang=lang).capitalize()
    
    if parte_decimal > 0:
        return f" {parte_entera_palabras} {parte_decimal:02d}/100 bolivianos."
    else:
        return f" {parte_entera_palabras} 00/100 bolivianos."

# Lista de códigos permitidos para gift cards (movido desde ui_copy.py)
GIFT_CARD_CODES = [
    102, 109, 115, 120, 124, 128, 129, 130, 138, 146, 153, 159, 164, 168,
    172, 173, 174, 182, 189, 195, 200, 204, 208, 209, 210, 217, 221, 222,
    223, 224, 225, 226, 228, 232, 241, 246, 250, 254, 255, 256, 261, 265,
    269, 270, 271, 275, 279, 280, 281, 285, 286, 287, 291, 292, 293, 30,
    304, 35, 40, 49, 53, 60, 64, 68, 72, 76, 77, 78, 86, 94, 27
]
