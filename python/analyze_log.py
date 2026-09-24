import math
def make_report():
    pixel_counter = 0
    hash_counter = 0
    fail_counter = 0

    with open("output.log", "r") as output:
        for line in output:
            if line.startswith("F"):
                pixel_counter += 1
            elif line.startswith("H"):
                hash_counter += 1
            elif line.startswith("T"):
                fail_counter += 1

    pixels = 1920 * 1080
    result_pixel = (((pixels) - pixel_counter) / pixels) * 100

    return [float("%.2f"%result_pixel), hash_counter, fail_counter]



