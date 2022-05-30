import math

import pikepdf
from fpdf import FPDF, ViewerPreferences
from PIL import Image
import os

from kf8comic import read_azw3

DEFAULT_DPI = 300
DEFAULT_DPM = DEFAULT_DPI / 25.4


def main(argv):
    if len(argv) < 3:
        print('Usage: python kf8pdf.py <ltr|rtl> <inputfile> [<outputfile>]')
        return

    rtl = argv[1] == 'rtl'

    input_file = argv[2]
    if len(argv) > 3:
        output = argv[3]
    else:
        output = os.path.splitext(input_file)[0] + '.pdf'

    # Read AZW3 file
    flat_toc, images, tmpdir = read_azw3(input_file)
    toc_map = {x[0]: x[1] for x in flat_toc}

    # Create PDF
    pdf = FPDF()
    pdf.set_display_mode('fullpage', 'two')
    pdf.set_margin(0)
    pdf.viewer_preferences = ViewerPreferences(hide_toolbar=True, hide_menubar=True, fit_window=True)

    print('Creating PDF...')

    skipped_next_image = False
    for i, image in enumerate(images):
        if skipped_next_image:
            skipped_next_image = False
            continue

        # Open with Pillow
        img = Image.open(image)
        width, height = img.size

        # Convert directly to mm
        width /= DEFAULT_DPM
        height /= DEFAULT_DPM

        pdf.add_page(format=(width, height))
        pdf.image(img, 0, 0, width, height)

        # Create TOC if present
        if (i + 1) in toc_map:
            pdf.start_section(toc_map[i + 1])

    pdf.output(output)

    # Set RTL and two-column reading
    with pikepdf.Pdf.open(output, allow_overwriting_input=True) as pdf:
        pdf.Root.PageLayout = pikepdf.Name.TwoPageRight
        if rtl:
            pdf.Root.ViewerPreferences.Direction = pikepdf.Name.R2L
        pdf.save()

    print('PDF saved to {}'.format(output))


if __name__ == '__main__':
    import sys
    main(sys.argv)
