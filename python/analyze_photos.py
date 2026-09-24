from PIL import Image
from datetime import datetime
from hashlib import sha256


def analyze(path1: str, path2: str):
    image_one = Image.open(path1)
    image_two = Image.open(path2)

    if image_one.size != image_two.size:
        with open ("output.log", "a") as output:
            output.write(f"\nS  -----    {image_one.filename} and {image_two.filename} size does not match\n")
            return -1


    else:

        hash_one = sha256(image_one.tobytes()).hexdigest()
        hash_two = sha256(image_two.tobytes()).hexdigest()

        if hash_one != hash_two:
            with open ("output.log", "a") as output:
                output.write(f"\nH  -----    {image_one.filename} and {image_two.filename} hash does not match -> {hash_one} != {hash_two}\n")

            for i in range(image_one.width):
                for j in range(image_one.height):

                    if image_one.getpixel((i, j)) != image_two.getpixel((i, j)):
                        with open ("output.log", "a") as output:
                            output.write(f"F  -----    There is a discrepancy at pixel: ({i}, {j})\n")


            info_one = image_one.info.items()
            info_two = image_two.info.items()

            if info_one != info_two:
                with open ("output.log", "a") as output:
                    output.write(f"\nMETADATA IMAGE_ONE:\n" 
                                 f"{info_one}\n" 
                                 f"METADATA IMAGE_TWO:\n" 
                                 f"{info_two}\n")




        


        else:
            with open ("output.log", "a") as output:
                output.write(f"C  -----    {image_one.filename} and {image_one.filename} have matching hashes -- IMAGES MATCH")





    

    