import os

fonts_dir = r"C:\Windows\Fonts"
ttf_fonts = [f for f in os.listdir(fonts_dir) if f.lower().endswith('.ttf')]
print("Fuentes TrueType instaladas:")
for font in ttf_fonts:
    print(font)