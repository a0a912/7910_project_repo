from generate_photos import generate_photos
from analyze_photos import analyze
from analyze_log import make_report

if __name__ == "__main__":
    result = generate_photos()

    if result == 1:
        path1 = "./photos/red1.png"
        path2 = "./photos/red2.png"
        analyze(path1, path2)
    elif result == -1:
        with open("output.log", "a") as output:
            output.write("TERMINATING EARLY ERROR OCCURED")

    results = make_report()
    print(f"Remaining Matching Pixels: {results[0]}%")
    print(f"Amount of Hashes that dont match: {results[1]}")
    print(f"Amount of failure tests (size not matching): {results[2]}")
