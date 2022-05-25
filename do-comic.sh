#!/bin/bash

# Script to extract image from calibre's ZIP format
# converted from AZW3 or EPUB

# Usage: ./do-comic.sh /path/to/manga.zip [-KPW5]
# The -KPW5 can be substitute for format to be used with KCC.
# Default is KPW5 (Kindle Paperwhite 2021)

# This script use this fork of KCC:
# https://github.com/darodi/kcc
# for better support of newer format and for mozjpeg
# (not that it matter for us, since Kindle Create convert JXR anyway)

KCC="/path/to/kcc/kcc-c2e.py"
SPREAD="./merge-spread.py"

# Get file name
NAME=${1%.*}

# Unzip to tmp folder
# This unzip only images and flatten the directory structure
unzip -jd "_tmp" "$1" "*.jpg" "*jpeg" "*.png"

# Do not process cover image
COVER=$(ls _tmp | grep cover)
mv "_tmp/$COVER" "_tmp_cover.${COVER##*.}"

# Try to merge double-page spread
python $SPREAD rtl "_tmp" "_tmp_merged"

# Run KCC to generate CBZ
# -m    Manga mode (right to left)
# -u    Upscale smaller image (some Kindle release is very low quality)
# -r 2  Rotate and split double page spread
# -c 1  Only crop margin, don't crop page number
#       The main reason is that margin crop has hard limit, while page number crop don't.
# --mozjpeg  Use mozjpeg for output
# -f CBZ  We wanted zip output, and CBZ is close enough
python $KCC -p ${2:-KPW5} -m -u -r 2 -c 1 --mozjpeg -f CBZ -o "_tmp.cbz" "_tmp_merged"

# Extracted CBZ to directory for Kindle Create
unzip "_tmp.cbz" -d "[KCC] $NAME"

# Restore cover image
mv "_tmp_cover.${COVER##*.}" "[KCC] $NAME/0000.${COVER##*.}"

# Clear all temp files
rm "_tmp.cbz"
rm -r "_tmp"
rm -r "_tmp_merged"
