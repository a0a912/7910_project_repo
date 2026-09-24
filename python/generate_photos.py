import re
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from distrupt_photos import distrupt



def generate_photos(paths: list[str]):

    colors = []
    width = 1920
    length = 1080
    

    for path in paths:
        match = re.search(r'/(red|blue|green|yellow|purple)\d+\.png$', path)

        if match and match.group(1) not in colors:
            colors.append(match.group(1))

    for x in colors:
        image = Image.new("RGB", (width, length), x)

        metadata = PngInfo()
        metadata.add_text("Author", "DDR4")
        metadata.add_text("Description", f"Solid {x} color")



        image.save(f"./photos/{x}1.png", pnginfo=metadata)
        image.save(f"./photos/{x}2.png", pnginfo=metadata)
        distrupt(f"./photos/{x}2.png", x)

    return 1
