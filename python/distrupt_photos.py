from PIL import Image
from PIL.PngImagePlugin import PngInfo
from datetime import datetime

def distrupt(path: str, color: str):
    bad_image = Image.open(path)

    metadata = PngInfo()
    metadata.add_text("Author", "DDR4")
    metadata.add_text("Description", f"Solid {color} color")

    for i in range(100, 200):
        bad_image.putpixel((i, i), (0, 255, 0))

    bad_image.save(path, pnginfo=metadata)