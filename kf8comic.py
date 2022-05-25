import tempfile
import os
import xml.etree.ElementTree as ET

from kindleunpack.kindleunpack import unpackBook


def read_metadata(path):
    # Metadata
    metadata_path = os.path.join(path, 'mobi8', 'OEBPS', 'content.opf')
    tree = ET.parse(metadata_path)
    root = tree.getroot()

    xmlns = {
        'opf': 'http://www.idpf.org/2007/opf',
        'dc': 'http://purl.org/dc/elements/1.1/',
    }

    title = root.find('.//dc:title', xmlns).text

    # Read spine
    spine = root.find('.//opf:spine', xmlns)
    spine_list = []
    for itemref in spine.findall('.//opf:itemref', xmlns):
        idref = itemref.get('idref')
        item = root.find('.//opf:item[@id="{}"]'.format(idref), xmlns)
        href = item.get('href')
        spine_list.append(href)

    xmlns = {
        'xhtml': 'http://www.w3.org/1999/xhtml',
        'svg': 'http://www.w3.org/2000/svg',
        'xlink': 'http://www.w3.org/1999/xlink',
    }

    # Read image from each page in spine
    images_list = []
    for page in spine_list:
        page_path = os.path.join(path, 'mobi8', 'OEBPS', page)
        tree = ET.parse(page_path)
        root = tree.getroot()
        for img in root.findall('.//svg:image', xmlns):
            src = img.get('{{{}}}href'.format(xmlns['xlink']))
            src = os.path.join(os.path.dirname(page_path), src)
            images_list.append((page, src))

    # Table of content
    toc = []
    ncx = os.path.join(path, 'mobi8', 'OEBPS', 'toc.ncx')
    tree = ET.parse(ncx)
    root = tree.getroot()

    xmlns = {
        'ncx': 'http://www.daisy.org/z3986/2005/ncx/',
    }

    for navpoint in root.findall('./ncx:navMap/ncx:navPoint', xmlns):
        title = navpoint.find('./ncx:navLabel/ncx:text', xmlns).text
        href = navpoint.find('./ncx:content', xmlns).get('src')
        order = navpoint.get('playOrder')
        toc.append((title, href, order))

    return title, images_list, toc


def make_flat_toc(images_list, toc):
    toc.sort(key=lambda x: int(x[2]))

    flat_toc = []
    toc_idx = 0
    cnt = 0
    for file, src in images_list:
        if file == toc[toc_idx][1]:
            flat_toc.append([cnt + 1, toc[toc_idx][0]])
            toc_idx += 1

            if toc_idx == len(toc):
                break

        cnt += 1

    return flat_toc


def read_azw3(filepath):
    tmpdir = tempfile.TemporaryDirectory()
    unpackBook(filepath, tmpdir.name)
    title, images_list, toc = read_metadata(tmpdir.name)
    flat_toc = make_flat_toc(images_list, toc)

    return flat_toc, [x[1] for x in images_list], tmpdir


if __name__ == '__main__':
    import sys
    flat_toc, images, _ = read_azw3(sys.argv[1])
    print(flat_toc)
    print(images)
