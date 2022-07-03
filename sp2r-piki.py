#!/usr/bin/env python
# Copyright (c) 2021, columbarius


import os
import argparse
import decimal

from pikepdf import Pdf, OutlineItem, Name, Dictionary, Page, make_page_destination, Object, Array, String


def pairwise(iterable):
    "s -> (s0, s1), (s2, s3), (s4, s5), ..."
    a = iter(iterable)
    return zip(a, a)


def calc_splitpage(page, split):
    width = page.MediaBox[2] - page.MediaBox[0]
    height = page.MediaBox[3] - page.MediaBox[1]
    return 0, width, split[0]*height, split[1]*height


def find_page_index(pdf, page):
    for idx in range(len(pdf.pages)):
        if page == pdf.pages[idx]:
            return idx
    os.abort()


def outline_parse_children(outlineItem, pdf_in, pdf_out, indent):
    # print(indent*" " + str(outlineItem))
    dict = outlineItem.to_dictionary_object(pdf_in, True)
    # help(dict)
    # print(dict.keys())
    # help(dict[Name.A].keys())
    # print(dict[Name.A].keys())
    # print(dict[Name.A][Name.S])
    # print(dict[Name.A][Name.D])
    # print(type(dict[Name.A][Name.D]))
    # os.abort()
    # print(indent*" " + str(vars(outlineItem.action)))
    # obj = OutlineItem(outlineItem.title)
    # dict = outlineItem.to_dictionary_object(pdf, True)
    # print(dict.get(Name.A).as_dict())
    action = Dictionary()
    action[Name.S] = dict[Name.A][Name.S]
    action[Name.D] = dict[Name.A][Name.D]

    obj = OutlineItem(outlineItem.title, action=action)
    # obj = OutlineItem(outlineItem.title)
    if isinstance(outlineItem.children, list):
        for child in outlineItem.children:
            obj.children.append(outline_parse_children(child, pdf_in, pdf_out, indent + 4))
    return obj


def outline_print_children(outlineItem, pdf, indent):
    print(indent*" " + str(outlineItem))
    dict = outlineItem.to_dictionary_object(pdf, True)
    # help(dict)
    # print(dict.keys())
    # help(dict[Name.A].keys())
    print(indent*" " + str(dict[Name.A].keys()) + ":" + "A=" + str(dict[Name.A][Name.S]) + "B=" + str(dict[Name.A][Name.D]))
    # print(type(dict[Name.A][Name.D]))
    # os.abort()
    # print(indent*" " + str(vars(outlineItem.action)))
    # obj = OutlineItem(outlineItem.title)
    # dict = outlineItem.to_dictionary_object(pdf, True)
    # print(dict.get(Name.A).as_dict())
    if isinstance(outlineItem.children, list):
        for child in outlineItem.children:
            outline_print_children(child, pdf, indent + 4)


def find_split(page, splits, pos_range):
    idx = 0
    for split in splits:
        width_min, width_max, height_min, height_max = calc_splitpage(page, split)
        if pos_range[1] > height_min and pos_range[1] < height_max:
            return idx
        idx += 1
    os.abort()


def migrate_named_destinations(pdf_in, pdf_out, splits):
    root_node = pdf_out.Root
    if Name.Names not in root_node:
        root_node[Name.Names] = Dictionary()
    if Name.Dests not in root_node[Name.Names]:
        root_node[Name.Names][Name.Dests] = Dictionary()
    if Name.Kids not in root_node[Name.Names][Name.Dests]:
        root_node[Name.Names][Name.Dests][Name.Kids] = Dictionary()

    name_node = root_node[Name.Names][Name.Dests][Name.Kids]
    for entry in pdf_in.Root[Name.Names][Name.Dests][Name.Kids]:
        print(2*" " + str(entry.keys()))
        entry_dest = Dictionary()
        entry_dest[Name.Kids] = Array()
        for subentry in entry[Name.Kids]:
            print(4*" " + str(subentry.keys()))
            subentry_dest = Dictionary()
            subentry_dest[Name.Kids] = Array()
            for subsubentry in subentry[Name.Kids]:
                print(6*" " + 12*"#")
                print(6*" " + str(subsubentry.keys()))
                subsubentry_dest = Dictionary()
                subsubentry_dest[Name.Names] = Array()
                for name_tuple in pairwise(subsubentry[Name.Names]):
                    name = name_tuple[0]
                    destination = name_tuple[1][Name.D]
                    page = Page(destination[0])
                    page_number = find_page_index(pdf_in, page)
                    pos_ind = destination[1]
                    pos_1 = destination[2]
                    pos_2 = destination[3]
                    whatever = destination[4]
                    split_num = find_split(page, splits, [pos_1, pos_2])
                    print(8*" " + 10*"*")
                    print(8*" " + str(name))
                    print(8*" " + str(page_number) + ":" + str(pos_ind) + ":" + str(pos_1) + ":" + str(pos_2) + ":" + str(whatever))
                    if (split_num >= 0):
                        print(8*" " + "Dest in split: " + str(split_num))
                    else:
                        print(8*" " + "Dest not in single split: " + str(split_num))
                    page_number_new = 2*page_number + split_num
                    print(8*" " + "New page number: " + str(page_number_new))
                    destination_new = make_page_destination(pdf_out, page_number_new)
                    subsubentry_dest[Name.Names].append(String(str(name)))
                    subsubentry_dest[Name.Names].append(destination_new)
                print(8*" " + 10*"*")
                subentry_dest[Name.Kids].append(subsubentry_dest)
            print(6*" " + 12*"#")
            entry_dest[Name.Kids].append(subentry_dest)
        name_node = entry_dest


def generate_split_pdf(pdf_in, splits):
    pdf_out = Pdf.new()
    for page in pdf_in.pages:
        for split in splits:
            pdf_out.pages.append(page)
            # print("MediaBox:" + str(page.MediaBox[0]) + ":" + str(page.MediaBox[1]) + ":" + str(page.MediaBox[2]) + ":" + str(page.MediaBox[3]))
            width_min, width_max, height_min, height_max = calc_splitpage(page, split)
            pdf_out.pages[-1].MediaBox = [width_min, height_min, width_max, height_max]
    with pdf_in.open_outline() as outline_in:
        outline_dst = []
        for outlineItem in outline_in.root:
            outline_print_children(outlineItem, pdf_in, 0)
            outline_dst.append(outline_parse_children(outlineItem, pdf_in, pdf_out, 0))
            # outline_dst.append(outlineItem)
        print("*****************************************************************************")
        with pdf_out.open_outline() as outline_out:
            outline_out.root.extend(outline_dst)
        migrate_named_destinations(pdf_in, pdf_out, splits)
        with pdf_out.open_outline() as outline_out:
            for outlineItem in outline_in.root:
                outline_print_children(outlineItem, pdf_out, 0)
    return pdf_out


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
    splits = [(decimal.Decimal('0.48'), decimal.Decimal('1')), (decimal.Decimal('0'), decimal.Decimal('0.52'))]

    pdf_in = Pdf.open(path_in)
    pdf_out = generate_split_pdf(pdf_in, splits)
    pdf_out.remove_unreferenced_resources()
    pdf_out.save(path_out)
