from PIL import Image
from PIL.PngImagePlugin import PngInfo
from distrupt_photos import distrupt
from datetime import datetime


def generate_photos():

    width = 1920
    length = 1080

    image = Image.new("RGB", (width, length), (255, 0, 0))

    metadata = PngInfo()
    metadata.add_text("Author", "DDR4")
    metadata.add_text("Description", f"Solid RED color")



    image.save("./photos/red1.png", pnginfo=metadata)
    image.save("./photos/red2.png", pnginfo=metadata)
    distrupt()

    return 1
