Below are three Python scripts that demonstrate the Plan B workflow: generating consistent 4K solid‑colour images with fixed metadata, simulating worst‑case corruption, and then verifying recovery by hash and pixel‑by‑pixel comparison.

**Dependencies:** Pillow (`pip install Pillow`).

---

## Script 1: `generate_images.py`

Creates two 4K PNG images (red and blue) with identical metadata, then prints the filename, metadata, and SHA256 hash.

```python
#!/usr/bin/env python3
"""
generate_images.py
Creates two 4K solid colour images (red and blue) with consistent metadata.
Prints filename, metadata, and SHA256 hash.
"""

from PIL import Image
from PIL.PngImagePlugin import PngInfo
import hashlib

WIDTH = 3840
HEIGHT = 2160

def create_solid_image(color, filename):
    img = Image.new("RGB", (WIDTH, HEIGHT), color)
    meta = PngInfo()
    meta.add_text("Creation Time", "2020-01-01 00:00:00")
    meta.add_text("Author", "Research Methodology")
    meta.add_text("Description", f"Solid {color} 4K image")
    img.save(filename, "PNG", pnginfo=meta)
    return filename

def file_hash(filename):
    h = hashlib.sha256()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    red_file = create_solid_image((255, 0, 0), "red.png")
    blue_file = create_solid_image((0, 0, 255), "blue.png")

    for f in [red_file, blue_file]:
        print(f"File: {f}")
        img = Image.open(f)
        print("  Metadata:")
        for k, v in img.info.items():
            print(f"    {k}: {v}")
        print(f"  SHA256: {file_hash(f)}")
        print()

if __name__ == "__main__":
    main()
```

---

## Script 2: `corrupt_images.py`

Randomly changes 5% of pixels in every PNG in the current directory. This simulates the “worst‑case” data loss and guarantees a different hash.

```python
#!/usr/bin/env python3
"""
corrupt_images.py
Randomly corrupts pixels in every PNG image in the current directory.
Simulates worst-case data loss.
"""

import os
import random
from PIL import Image

CORRUPT_PERCENT = 5.0  # percentage of pixels to corrupt

def corrupt_image(filename):
    img = Image.open(filename)
    pixels = img.load()
    width, height = img.size
    total = width * height
    num_to_corrupt = int(total * CORRUPT_PERCENT / 100)

    for _ in range(num_to_corrupt):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        pixels[x, y] = (random.randint(0, 255),
                        random.randint(0, 255),
                        random.randint(0, 255))

    img.save(filename)
    print(f"Corrupted {filename}: {num_to_corrupt} pixels changed.")

def main():
    for f in os.listdir("."):
        if f.lower().endswith(".png"):
            corrupt_image(f)

if __name__ == "__main__":
    main()
```

---

## Script 3: `check_recovery.py`

Compares images in the current folder against reference originals in a specified directory.  
- If SHA256 hashes match → **perfect recovery**.  
- Otherwise, it compares every pixel and reports the percentage of pixels that are exactly the same.

```python
#!/usr/bin/env python3
"""
check_recovery.py
Compares images in current folder against reference images in a reference folder.
If SHA256 matches -> perfect recovery.
Else -> pixel-by-pixel comparison, reports % recovery.
Usage: python check_recovery.py [reference_dir]
Default reference_dir = "originals"
"""

import sys
import os
import hashlib
from PIL import Image

def file_hash(filename):
    h = hashlib.sha256()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def compare_pixels(ref_file, test_file):
    ref = Image.open(ref_file)
    test = Image.open(test_file)
    if ref.size != test.size:
        print(f"  Size mismatch: ref {ref.size}, test {test.size}")
        return 0.0

    ref_pixels = ref.load()
    test_pixels = test.load()
    width, height = ref.size
    total = width * height
    matches = 0

    for y in range(height):
        for x in range(width):
            if ref_pixels[x, y] == test_pixels[x, y]:
                matches += 1

    return (matches / total) * 100.0

def main():
    ref_dir = sys.argv[1] if len(sys.argv) > 1 else "originals"
    if not os.path.isdir(ref_dir):
        print(f"Reference directory not found: {ref_dir}")
        sys.exit(1)

    for f in os.listdir("."):
        if not f.lower().endswith(".png"):
            continue
        test_path = os.path.join(".", f)
        ref_path = os.path.join(ref_dir, f)
        if not os.path.exists(ref_path):
            print(f"No reference for {f}, skipping.")
            continue

        print(f"Checking {f}...")
        h_test = file_hash(test_path)
        h_ref = file_hash(ref_path)

        if h_test == h_ref:
            print("  Perfect recovery! Hashes match.")
        else:
            print("  Hash mismatch. Comparing pixels...")
            pct = compare_pixels(ref_path, test_path)
            print(f"  Recovery: {pct:.2f}% of pixels match.")

if __name__ == "__main__":
    main()
```

---

## How to demo

1. **Generate originals**  
   ```bash
   python generate_images.py
   ```
   This creates `red.png` and `blue.png` in the current directory.

2. **Save a pristine copy**  
   ```bash
   mkdir originals
   cp red.png blue.png originals/
   ```

3. **Corrupt the working copies**  
   ```bash
   python corrupt_images.py
   ```
   `red.png` and `blue.png` in the current directory are now randomly corrupted.

4. **Check recovery**  
   ```bash
   python check_recovery.py originals
   ```
   You will see output like:
   ```
   Checking red.png...
     Hash mismatch. Comparing pixels...
     Recovery: 95.00% of pixels match.
   Checking blue.png...
     Hash mismatch. Comparing pixels...
     Recovery: 94.98% of pixels match.
   ```

This demonstrates the exact pipeline you need: consistent originals → simulated loss → hash check → pixel‑level recovery percentage.

For the real USB experiment, replace the corruption step with actual `ddrescue` + file carving, then point `check_recovery.py` at the original generated images and the recovered ones.
