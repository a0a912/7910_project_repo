from PIL import Image
from distrupt_photos import distrupt

def generate_photos():

    width = 1920
    length = 1080

    image = Image.new("RGB", (width, length), (255, 0, 0))

    image.save("./photos/red1.png")
    image.save("./photos/red2.png")
    distrupt()

    return 1
