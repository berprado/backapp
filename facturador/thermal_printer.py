from PIL import Image, ImageDraw, ImageFont
from escpos.printer import Usb

class ThermalPrinter:
    def __init__(self, vendor_id=0x04B8, product_id=0x0E15):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.line_width = 384  # Ancho en px para imágenes en impresoras térmicas

    def render_text_to_image(self, text, font_path="arial.ttf", font_size=12, line_spacing=1):
        """
        Renderiza texto a una imagen con el tamaño de fuente especificado.
        :param text: Texto a renderizar
        :param font_path: Ruta a la fuente TrueType
        :param font_size: Tamaño de la fuente en px
        :param line_spacing: Espaciado entre líneas
        """
        # Cargar la fuente
        font = ImageFont.truetype(font_path, font_size)
        lines = text.split("\n")

        # Calcular dimensiones del lienzo
        max_line_width = max(font.getbbox(line)[2] for line in lines)  # Usamos getbbox
        height = (font_size + line_spacing) * len(lines)
        width = max(max_line_width, self.line_width)

        # Crear la imagen
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        # Dibujar texto
        y = 0
        for line in lines:
            draw.text((0, y), line, font=font, fill="black")
            y += font_size + line_spacing

        return image


    def print_image(self, image):
        """
        Imprime una imagen en la impresora térmica.
        :param image: Objeto de imagen PIL
        """
        try:
            printer = Usb(self.vendor_id, self.product_id)  # Crear la instancia de la impresora
            printer.image(image)  # Imprimir la imagen
            printer.cut()  # Cortar el papel
        except Exception as e:
            print(f"Error al imprimir la imagen: {e}")
            raise
        finally:
            try:
                printer.close()  # Cerrar la conexión
            except Exception:
                pass


    def print_html_as_image(self, html_content, font_path="arial.ttf", font_size=10):
        """
        Convierte contenido HTML a texto plano y lo renderiza como imagen para imprimir.
        :param html_content: Contenido HTML como string
        :param font_path: Ruta a la fuente TrueType
        :param font_size: Tamaño de la fuente en px
        """
        from bs4 import BeautifulSoup

        # Extraer texto del HTML
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text()

        # Renderizar el texto a una imagen
        image = self.render_text_to_image(text, font_path=font_path, font_size=font_size)

        # Imprimir la imagen
        self.print_image(image)
