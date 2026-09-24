from PIL import Image

def distrupt():
    bad_image = Image.open("./photos/red2.png")

    for i in range(100, 200):
        bad_image.putpixel((i, i), (0, 255, 0))

    bad_image.save("./photos/red2.png")