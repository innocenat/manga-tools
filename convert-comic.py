#!/usr/bin/env python3

from PIL import Image
import os
import io
import numpy as np
import mozjpeg_lossless_optimization

from kf8comic import read_azw3

GAMMA = 1.8
PALETTE = [
    0x00, 0x00, 0x00,
    0x11, 0x11, 0x11,
    0x22, 0x22, 0x22,
    0x33, 0x33, 0x33,
    0x44, 0x44, 0x44,
    0x55, 0x55, 0x55,
    0x66, 0x66, 0x66,
    0x77, 0x77, 0x77,
    0x88, 0x88, 0x88,
    0x99, 0x99, 0x99,
    0xaa, 0xaa, 0xaa,
    0xbb, 0xbb, 0xbb,
    0xcc, 0xcc, 0xcc,
    0xdd, 0xdd, 0xdd,
    0xee, 0xee, 0xee,
    0xff, 0xff, 0xff,
]

PAL_IMG = Image.new('P', (1, 1))
PAL_IMG.putpalette(PALETTE)

ALL = 0


def calculate_image_size(image, d_width, d_height):
    width, height = image.size
    ratio = min(d_width / width, d_height / height)
    new_width = int(width * ratio)
    new_height = int(height * ratio)
    return new_width, new_height


def contrast_gamma(image):
    data = np.array(image.getdata())
    data = np.divide(data, 255)
    data = np.clip(data, 0, 1)
    data = np.power(data, GAMMA)
    min_, max_ = np.amin(data), np.amax(data)
    if min_ != max_:
        data = np.subtract(data, min_)
        data = np.multiply(data, 255 / (max_ - min_))
    else:
        data = np.multiply(data, 255)
    image.putdata(data)
    return image


# Process individual image (must be after double-spread is split)
def process_image_inner(image, d_width, d_height):
    # First, convert to floating point (greyscale)
    img = image.convert('F', dither=Image.FLOYDSTEINBERG)

    # Then, resize
    new_width, new_height = calculate_image_size(image, d_width, d_height)
    img = img.resize((new_width, new_height), Image.LANCZOS)

    # Then, apply gamma
    img = contrast_gamma(img)

    # Then, quantize
    img = img.convert('L')
    img = img.convert('RGB')
    img = img.quantize(colors=len(PALETTE) / 3, palette=PAL_IMG, dither=Image.FLOYDSTEINBERG)
    img = img.convert('RGB')

    return img


def process_image(image, d_width, d_height):
    if image.width < image.height:
        return [process_image_inner(image, d_width, d_height)]

    # Split into two
    left = image.width // 2
    return [process_image_inner(x, d_width, d_height) for x in
            [image.crop((left, 0, image.width, image.height)), image.crop((0, 0, left, image.height))]]


def save_image_mozjpeg(image, output_dir, i, extra=''):
    filename = os.path.join(output_dir, '{:05d}{}.jpg'.format(i + 1, extra))
    with io.BytesIO() as output:
        image.save(output, format="JPEG", optimize=1, quality=85)
        input_jpeg_bytes = output.getvalue()
        output_jpeg_bytes = mozjpeg_lossless_optimization.optimize(input_jpeg_bytes)
        with open(filename, "wb") as output_jpeg_file:
            output_jpeg_file.write(output_jpeg_bytes)


def process_and_save_image(image, i, output_dir, d_width, d_height):
    # Process image
    images = process_image(image, d_width, d_height)
    if len(images) == 1:
        save_image_mozjpeg(images[0], output_dir, i)
    else:
        for idx, image in enumerate(images):
            save_image_mozjpeg(image, output_dir, i, extra='-{}'.format(idx))


def process_and_save_image_pooled(args):
    image, i, output_dir, d_width, d_height = args
    process_and_save_image(image, i, output_dir, d_width, d_height)


def directory_generator(input_dir):
    import glob
    files = [x for e in ['jpg', 'jpeg', 'png', 'gif'] for x in
             glob.glob(os.path.join(input_dir, '**', '*.{}'.format(e)), recursive=True)]
    files.sort()

    global ALL
    ALL = len(files)

    return ((i, Image.open(x)) for i, x in enumerate(files))


def zip_generator(input_zip):
    import zipfile
    images_file = []
    with zipfile.ZipFile(input_zip, 'r') as zip_ref:
        for info in zip_ref.infolist():
            if info.filename.endswith('.jpg') or info.filename.endswith('.jpeg') or info.filename.endswith('.png'):
                images_file.append(info.filename)

        # Sort image file
        images_file.sort()

        global ALL
        ALL = len(images_file)

        # Process image file
        for i, file in enumerate(images_file):
            image_blob = zip_ref.read(file)
            image_io = io.BytesIO(image_blob)
            image = Image.open(image_io)
            yield i, image


def azw3_generator(input_azw3):
    flat_toc, images, tmpdir = read_azw3(input_azw3)

    print('AZW3 Table of Content:')
    for x in flat_toc:
        print('  {:5d}: {}'.format(*x))
    print()

    global ALL
    ALL = len(images)

    for i, image in enumerate(images):
        yield i, Image.open(image)


def process_with_generator(generator, output_dir, d_width, d_height):
    from multiprocessing import Pool
    os.makedirs(output_dir, exist_ok=True)
    with Pool() as pool:
        r = pool.imap_unordered(process_and_save_image_pooled,
                                ((image, i, output_dir, d_width, d_height) for i, image in generator))

        # Drain the pool
        CNT = 0
        print('Processing images...', end='\r', flush=True)
        for x in r:
            CNT += 1
            print('Processing images... {:5d}/{}'.format(CNT, ALL), end='\r', flush=True)
        print('Done!                               ')


def main(argv):
    if len(argv) < 5:
        print('Usage: python convert-comic.py <width> <height> <input-dir> <output-dir>')
        return

    width = int(argv[1])
    height = int(argv[2])

    print('convert-comic.py: Comic Preparation tool for Kindle Create')
    print('  size: {}x{}'.format(width, height))
    print()

    if not os.path.exists(argv[3]):
        print('Input does not exist: {}'.format(argv[3]), file=sys.stderr)
        return

    if os.path.exists(argv[4]) and not os.path.isdir(argv[4]):
        print('Output is not a directory: {}'.format(argv[4]), file=sys.stderr)
        return

    generator = None

    if os.path.isdir(argv[3]):
        generator = directory_generator(argv[3])
    else:
        _, ext = os.path.splitext(argv[3])
        if ext == '.zip' or ext == '.cbz':
            generator = zip_generator(argv[3])
        if ext == '.azw3':
            generator = azw3_generator(argv[3])

    if generator is None:
        print('Unsupported input file type: {}'.format(argv[3]), file=sys.stderr)
        print('Supported file types: directory, zip, cbz, azw3', file=sys.stderr)
        return

    process_with_generator(generator, argv[4], width, height)


if __name__ == '__main__':
    import sys

    main(sys.argv)
