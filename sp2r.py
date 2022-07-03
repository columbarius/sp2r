#!/usr/bin/env python
# Copyright (c) 2021, columbarius


import os
import argparse
import decimal

from PyPDF2 import PdfFileReader, PdfFileWriter


def pdf_splitter(path_in, i, j):
    fname = os.path.splitext(os.path.basename(path_in))[0]

    pdf = PdfFileReader(path_in)
    pdf_writer = PdfFileWriter()

    page_width = pdf.getPage(0).mediaBox.lowerRight[0] - pdf.getPage(0).mediaBox.lowerLeft[0]
    page_height = pdf.getPage(0).mediaBox.upperLeft[1] - pdf.getPage(0).mediaBox.lowerLeft[1]

    for page_num in range(pdf.getNumPages()):
        page = pdf.getPage(page_num)
        pdf_writer.addPage(page)

        pdf_writer.getPage(page_num).cropBox.upperLeft = (page.mediaBox.upperLeft[0], page.mediaBox.upperLeft[1] - i * page_height)
        pdf_writer.getPage(page_num).cropBox.lowerRight = (page.mediaBox.lowerRight[0], page.mediaBox.upperRight[1] - j * page_height)

    path_out = str(i) + "_" +  str(j) + "_" + path_in
    out = open(path_out, 'wb')
    pdf_writer.write(out)
    return path_out

def show_tree(bookmark_list, pdf_in, indent=0):
    for item in bookmark_list:
        if isinstance(item, list):
            # recursive call with increased indentation
            show_tree(item, pdf_in, indent + 4)
        else:
            print(" " * indent + item.title)
            print(" " * indent + str(pdf_in.getDestinationPageNumber(item)))
            print(" " * indent + str(item.top))
            print(" " * indent + str(item.bottom))
            print(" " * indent + str(item.left))
            print(" " * indent + str(item.right))

def merge_bookmarks(pdf_in, pdf_out):
    show_tree(pdf_in.getOutlines(), pdf_in)


def pdf_merge(path_in, path_out, pdfs):
    pdf_list = []
    for pdf in pdfs:
        pdf_list.append(PdfFileReader(pdf))
    pdf_writer = PdfFileWriter()
    pdf_orig = PdfFileReader(path_in)

    for page_num in range(pdf_list[0].getNumPages()):
        for pdf in pdf_list:
            pdf_writer.addPage(pdf.getPage(page_num))

    merge_bookmarks(pdf_orig, pdf_writer)

    out = open(path_out, 'wb')
    pdf_writer.write(out)
    for pdf in pdfs:
        os.remove(pdf)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Splits pdf pages into multiple pages with overlap for better presentation on ebook readers and similar devices")
    parser.add_argument('--usage', action='store_true')
    parser.add_argument('-i', '--input', default="in.pdf")
    parser.add_argument('-o', '--output', default="out.pdf")

    args = parser.parse_args()

    if args.usage:
        parser.print_usage()
        exit(0)

    path_in = args.input
    path_out = args.output
    pdf_splits = []
    splits = [(decimal.Decimal('0'), decimal.Decimal('0.52')), (decimal.Decimal('0.48'), decimal.Decimal('1'))]
    for diff in splits:
        pdf_splits.append(pdf_splitter(path_in, diff[0], diff[1]))
    pdf_merge(path_in, path_out, pdf_splits)
