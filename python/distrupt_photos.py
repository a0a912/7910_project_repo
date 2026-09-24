from PIL import Image
from PIL.PngImagePlugin import PngInfo
from datetime import datetime

def distrupt():
    bad_image = Image.open("./photos/red2.png")

    metadata = PngInfo()
    metadata.add_text("Author", "DDR4")
    metadata.add_text("Description", f"Solid RED color")

    for i in range(100, 200):
        bad_image.putpixel((i, i), (0, 255, 0))

    bad_image.save("./photos/red2.png", pnginfo=metadata)