from generate_photos import generate_photos
from analyze_photos import analyze
from analyze_log import make_report

if __name__ == "__main__":
    
    paths = ["./photos/red1.png", "./photos/red2.png", "./photos/blue1.png", "./photos/blue2.png",
             "./photos/green1.png", "./photos/green2.png", "./photos/yellow1.png", "./photos/yellow2.png",
             "./photos/purple1.png", "./photos/purple2.png"]

    
    result = generate_photos(paths)



    if result == 1:
        for x in range(0, 10, 2): 
            analyze(paths[x], paths[x + 1])
    elif result == -1:
        with open("output.log", "a") as output:
            output.write("TERMINATING EARLY ERROR OCCURED")

    results = make_report()
    print(f"Remaining Matching Pixels: {results[0]}%")
    print(f"Amount of Hashes that dont match: {results[1]}")
    print(f"Amount of failure tests (size not matching): {results[2]}")
