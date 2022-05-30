#!/usr/bin/env python3

from PIL import Image
import glob
import os
import math
import shutil


# Convert color to linear light according to sRGB
def c_lin(c):
    c /= 255
    if c <= 0.04045:
        return c / 12.92
    else:
        return ((c + 0.055) / 1.055) ** 2.4


# Calculate Root Mean Squared (RMS) of the list
def rms(l):
    return math.sqrt(sum([x**2 for x in l]) / len(l))


# Calculate contrast of the spread between two images
# Return: percentage of that is used to calculate, contrast
#
# We calculate the contrast along the seam of the page,
# ignoring the background color (white or black).
def calculate_spread_contrast(direction, f0, f1):
    if f0.height != f1.height:
        return 0, 0

    x0 = f0.width - 1
    x1 = 0
    if direction == -1:
        x0 = 0
        x1 = f1.width - 1

    if f0.mode != 'RGB':
        f0 = f0.convert('RGB')

    if f1.mode != 'RGB':
        f1 = f1.convert('RGB')

    ca, cb = [], []
    for y in range(f0.height):
        [r0, g0, b0] = [c_lin(x) for x in f0.getpixel((x0, y))]
        [r1, g1, b1] = [c_lin(x) for x in f1.getpixel((x1, y))]

        # Calculate luminance
        y0 = 0.2126*r0 + 0.7152*g0 + 0.0722*b0
        y1 = 0.2126*r1 + 0.7152*g1 + 0.0722*b1

        # Ignore white background
        if y0 < 0.95 and y1 < 0.95:
            ca.append(abs(y0 - y1))

        # Ignore black background
        if 0.05 < y0 and 0.05 < y1:
            cb.append(abs(y0 - y1))

    # If all the pixels are white or black, return 0
    if len(ca) == 0 or len(cb) == 0:
        return 0, 0

    # Return whichever has less percentage of content compared to background
    if len(ca) < len(cb):
        return len(ca) / f0.height, rms(ca)
    else:
        return len(cb) / f0.height, rms(cb)


# Merge to image together
def merge_image(f0, f1, direction):
    if f0.height != f1.height:
        return None
    img = Image.new('RGB', (f0.width + f1.width, f0.height))
    if direction == 1:
        img.paste(f0, (0, 0))
        img.paste(f1, (f0.width, 0))
    else:
        img.paste(f1, (0, 0))
        img.paste(f0, (f1.width, 0))
    return img


def main(argv):
    if len(argv) < 4:
        print('Usage: python merge_spread.py <ltr|rtl> <inputdirectory> <outputfile>')
        return

    if argv[1] == 'ltr':
        direction = 1
    elif argv[1] == 'rtl':
        direction = -1
    else:
        print('Usage: python merge_spread.py <ltr|rtl> <inputdirectory> <outputfile>')
        return

    input_dir = glob.escape(argv[2])
    files = glob.glob(os.path.join(input_dir, '*.jpg')) + glob.glob(os.path.join(input_dir, '*.jpeg')) + glob.glob(os.path.join(input_dir, '*.png'))
    files = list(sorted(files))

    if len(files) == 0:
        print('No image files found')
        return

    output_path = argv[3]
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    if not os.path.isdir(output_path):
        print('Output path is not a directory')
        return

    f0 = Image.open(files[0])
    skipped_next_file = False

    # Try all pairs of page
    for i in range(1, len(files)):
        f1 = Image.open(files[i])

        if skipped_next_file:
            # Current page f0 has already been use in a double-page spread, skipping
            skipped_next_file = False
        else:
            # Check contrast
            pct, contrast = calculate_spread_contrast(direction, f0, f1)

            # This is arbitrary threshold, but it seems to work well
            if pct > 0.15 and contrast < 0.25:
                print('{} {} {:2.0f}%  {:.2f}'.format(files[i-1], files[i], pct*100, contrast))
                img = merge_image(f0, f1, direction)
                img_name = os.path.splitext(os.path.basename(files[i-1]))[0] + '-' + os.path.splitext(os.path.basename(files[i]))[0] + os.path.splitext(os.path.basename(files[i-1]))[1]
                img.save(os.path.join(output_path, img_name))
                skipped_next_file = True
            else:
                # Otherwise, just copy the file
                shutil.copy2(files[i-1], os.path.join(output_path, os.path.basename(files[i-1])))

        f0.close()
        f0 = f1

    f0.close()

    if not skipped_next_file:
        shutil.copy2(files[-1], os.path.join(output_path, os.path.basename(files[-1])))


if __name__ == '__main__':
    import sys
    main(sys.argv)
