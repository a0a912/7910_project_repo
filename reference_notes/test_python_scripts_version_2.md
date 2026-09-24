These Python scripts use the `Pillow` library (`pip install Pillow`) for image processing.

A critical detail for your team's "Plan B": **You must use lossless formats like PNG.** If you use JPEG, the format's inherent lossy compression will instantly alter pixel colors upon saving, which will change the hash and fail your pixel-by-pixel check before the filesystem even touches it.

Here is the three-script demonstration pipeline.

### Script 1: The Generator (`1_generate_images.py`)

This script creates the 4K solid-color PNGs, embeds a creation date into the PNG metadata, hashes the file, and saves the baseline data to a JSON file so the verification script knows what to expect.

```python
import os
import hashlib
import json
from PIL import Image
from PIL.PngImagePlugin import PngInfo

WORK_DIR = "recovery_test_images"
os.makedirs(WORK_DIR, exist_ok=True)

# Define our target images and their exact RGB values
IMAGES_TO_CREATE = {
    "red_4k.png": (255, 0, 0),
    "blue_4k.png": (0, 0, 255)
}
RESOLUTION = (3840, 2160)
METADATA_DATE = "2020:01:01 12:00:00"

def get_sha256(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

def main():
    baseline_data = {}

    for filename, color in IMAGES_TO_CREATE.items():
        filepath = os.path.join(WORK_DIR, filename)
        
        # 1. Create solid color image
        img = Image.new("RGB", RESOLUTION, color)
        
        # 2. Inject preset metadata
        metadata = PngInfo()
        metadata.add_text("Creation Time", METADATA_DATE)
        
        # 3. Save as lossless PNG
        img.save(filepath, "PNG", pnginfo=metadata)
        
        # 4. Hash the generated file
        file_hash = get_sha256(filepath)
        
        # 5. Store baseline data
        baseline_data[filename] = {
            "expected_hash": file_hash,
            "target_color": color,
            "total_pixels": RESOLUTION[0] * RESOLUTION[1]
        }
        
        print(f"Generated: {filename}")
        print(f"  -> Color: RGB{color}")
        print(f"  -> Metadata Date: {METADATA_DATE}")
        print(f"  -> SHA-256: {file_hash}\n")

    # Save baseline to JSON for Script 3
    with open(os.path.join(WORK_DIR, "baseline.json"), "w") as f:
        json.dump(baseline_data, f, indent=4)
        print("Baseline data saved to baseline.json")

if __name__ == "__main__":
    main()

```

### Script 2: The Corruptor (`2_corrupt_images.py`)

This script simulates a fragmented or partially overwritten recovery. It opens every PNG in the folder and overwrites a random number of pixels with static (random RGB values), ensuring the file hash changes and simulating sector damage.

```python
import os
import random
from PIL import Image

WORK_DIR = "recovery_test_images"
CORRUPTION_AMOUNT = 50000  # Number of pixels to randomly change

def main():
    if not os.path.exists(WORK_DIR):
        print(f"Directory '{WORK_DIR}' not found. Run Script 1 first.")
        return

    for filename in os.listdir(WORK_DIR):
        if not filename.endswith(".png"):
            continue
            
        filepath = os.path.join(WORK_DIR, filename)
        img = Image.open(filepath)
        pixels = img.load()
        width, height = img.size
        
        # Introduce random noise to simulate data loss/overwrites
        for _ in range(CORRUPTION_AMOUNT):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            # Replace pixel with random RGB noise
            pixels[x, y] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            
        # Resave the corrupted image
        # Note: In a real environment, you wouldn't use PngInfo here to simulate losing metadata
        img.save(filepath, "PNG")
        print(f"Corrupted {CORRUPTION_AMOUNT} pixels in {filename}")

if __name__ == "__main__":
    main()

```

### Script 3: The Analyzer (`3_analyze_recovery.py`)

This script checks the current hashes against the JSON baseline. If the hash fails, it utilizes Pillow's `getcolors()` method (which is highly optimized in C) to rapidly count exactly how many pixels survived unscathed, giving you a precise percentage of recovery.

```python
import os
import json
import hashlib
from PIL import Image

WORK_DIR = "recovery_test_images"

def get_sha256(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

def main():
    baseline_path = os.path.join(WORK_DIR, "baseline.json")
    if not os.path.exists(baseline_path):
        print("baseline.json not found. Run Script 1 first.")
        return

    with open(baseline_path, "r") as f:
        baseline_data = json.load(f)

    for filename, data in baseline_data.items():
        filepath = os.path.join(WORK_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"[{filename}] MISSING: File was not recovered at all (0.00%).")
            continue
            
        current_hash = get_sha256(filepath)
        
        # 1. Hash Check (Perfect Recovery)
        if current_hash == data["expected_hash"]:
            print(f"[{filename}] PERFECT RECOVERY (100.00%) - Hashes match.")
            continue
            
        # 2. Pixel-by-Pixel Verification (Partial Recovery)
        print(f"[{filename}] PARTIAL RECOVERY - Hashes differ. Analyzing pixels...")
        img = Image.open(filepath)
        target_color = tuple(data["target_color"])
        total_pixels = data["total_pixels"]
        
        # getcolors(maxcolors) returns a list of (count, color) tuples. 
        # Using total_pixels as maxcolors ensures it doesn't error out on highly corrupted files.
        color_counts = img.getcolors(maxcolors=total_pixels)
        
        # Find the count of our specific original color
        surviving_pixels = 0
        if color_counts:
            for count, color in color_counts:
                # Pillow might return RGBA, so we match the first 3 channels
                if color[:3] == target_color:
                    surviving_pixels = count
                    break
        
        recovery_percentage = (surviving_pixels / total_pixels) * 100
        lost_pixels = total_pixels - surviving_pixels
        
        print(f"  -> Total Pixels: {total_pixels}")
        print(f"  -> Survived:     {surviving_pixels}")
        print(f"  -> Corrupted:    {lost_pixels}")
        print(f"  -> Score:        {recovery_percentage:.4f}%\n")

if __name__ == "__main__":
    main()

```

When integrating this into your bash automation, how are you planning to mount and pass the carved files from `ddrescue` or `PhotoRec` into this Python verification directory?
