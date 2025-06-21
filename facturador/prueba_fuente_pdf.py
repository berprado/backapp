from weasyprint import HTML

html = '''
<html>
  <head>
    <meta charset="utf-8">
    <style>
      body { font-family: Arial, sans-serif; }
      h1 { color: #2E86C1; }
      p { font-size: 18px; }
    </style>
  </head>
  <body>
    <h1>Prueba de fuente Arial</h1>
    <p>Si ves este texto en Arial y en color azul, la fuente está disponible y el renderizado funciona.</p>
    <p>Fecha de prueba: 21/06/2025</p>
  </body>
</html>
'''

HTML(string=html).write_pdf("test_fuente_arial.pdf")
print("PDF generado: test_fuente_arial.pdf")
