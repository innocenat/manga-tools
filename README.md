# Manga processing tool

These are tools I used for processing manga to read on my Kindle
e-ink device. It might be useful for other so I decided to share.

Note that this is for manga. That means almost everything assume
right-to-left reading. Feel free to modify it to suit your needs.

These scripts are mostly written to help create KFX Manga
with Kindle Create. If you don't care about KFX Manga, just use
[Kindle Comic Converter](https://kcc.iosphe.re/) which is all-in-one
solution.

KFX Manga on Kindle e-reader device will enable *Kindle Manga Experience*.
This enabled Ultra-Fast Skimming and faster page turn feature on the
Kindle.

### merge-spread.py
This tool use heuristics to merge double-page spread from different
file into single image. This is useful for pro-processing images
extracted from EPUB/AZW3 to be used with Kindle Comic Converter (KCC).

### do-comic.sh
A shell script to process ZIP manga file from Calibre into image files
for use with Kindle Create. Abandoned when I realized Kindle will
automatically display double-page spread even for 3rd party file.

This should be trivially modified if you want to output EPUB for use
with other readers, etc.

### convert-comic.py

This is a standalone Python script to prepare image files for
Kindle Create. It accepts directory structure, ZIP, CBZ, and AZW3.

The AZW3 reader used [KindleUnpack](https://github.com/kevinhendricks/KindleUnpack)
tool to extract images from AZW3, with code located in `kf8comic.py`.
It basically just run kindleunpack into tmp directory and read the 
EPUB structure generated.
