#!/usr/bin/env python3

#
# Name: rmdc
# Author: Vít Černý
# License: GPL v3
#
# -*- coding: utf-8 -*-

import argparse
import re
import os
import shutil

LINK_PATTERN = re.compile("\[\[(.*?)\]\]")
ITALIC_PATTERN = re.compile("__(.*?)__")
HIGHLIGHT_PATTERN = re.compile("\^\^(.*?)\^\^")
ALIAS_PATTERN = re.compile("\[(.*?)\]\(\[\[(.*?)\]\]\)")

def parse_args():
    "Parse and return command line arguments"
    parser = argparse.ArgumentParser(description="Share your markdown notes in context.")
    parser.add_argument("-f", "--file", type=str, help="Target filename", required=True)
    parser.add_argument("-x", "--exclude", nargs='+', help="FILENAMES to exclude", default=[])
    parser.add_argument("-d", "--depth", type=int, help="Depth of recursion", required=True)
    parser.add_argument("-i", "--input-dir", type=str, default=".", help="Path to input directory with your notes")
    parser.add_argument("-o", "--output-dir", type=str, help="Path to output directory", required=True)
    parser.add_argument("-w", "--web", type=str, help="Convert wikilinks to simple weblinks and sanitize roam markdown, argument is the notes directory")
    parser.add_argument("-e", "--empty",action="store_true", help="Exclude empty notes")
    return parser.parse_args()


def scan_file(filename):
    "Scan a markdown file and return filenames"
    try:
        file = open(filename)
    except FileNotFoundError:
        print("File for note '" + filename + "' does not exist! Skipping...\n")
        return
    linked_notes = re.findall(LINK_PATTERN, file.read())
    return [x + ".md" for x in linked_notes]


def copy_notes(notes, directory):
    "copy all selected notes to a directory"
    try:
        os.mkdir(directory)
    except FileExistsError:
        print("Directory '" + directory + "' already exists!")
        if (input("Do you want to delete the directory? (y/n) ") == "y"):
            shutil.rmtree(directory)
            os.mkdir(directory)
        else:
            print("Aborting...")
            return
    for item in notes:
        shutil.copy(item, directory)
    print(str(len(notes)), "files successfully copied into directory '" + directory + "'")


def urlize(name: str):
    "Urlize a link (as Hugo does)"
    return name.lower().replace(" ", "-")


def webify(content: str, existing_pages, web_dir):
    "Change wikilinks to simple web links for my website"
    aliases = re.findall(ALIAS_PATTERN, content)
    for alias in aliases:
        full_alias =  "[" + alias[0] + "]" + "([[" + alias[1] + "]])"
        if alias[1] in existing_pages:
            content = content.replace(full_alias, full_alias.replace("[[" + alias[1] + "]]", urlize(os.path.join(web_dir, alias[1]))))
        else:
            content = content.replace(full_alias, alias[0])
    links = re.findall(LINK_PATTERN, content)
    for link in links:
        full_link = "[[" + link + "]]"
        if link in existing_pages:
            content = content.replace(full_link, ("[" + link + "]" + urlize("(" + os.path.join(web_dir, link) + ")")))
        else:
            content = content.replace(("[[" + link + "]]"), link)
    italics = re.findall(ITALIC_PATTERN, content)
    for italic in italics:
        full_italic = "__" + italic + "__"
        content = content.replace(full_italic, "_" + italic + "_")
    highlights = re.findall(HIGHLIGHT_PATTERN, content)
    for highlight in highlights:
        full_highlight = "^^" + highlight + "^^"
        content = content.replace(full_highlight, "<mark>" + highlight + "</mark>")
    return content


def main():
    args = parse_args()
    print("Following notes will be excluded: ")
    for item in args.exclude:
        print("- " + item)
    print("\nStarting with note:", args.file, "\n")

    final_files = [os.path.join(args.input_dir, args.file)]
    target_files = final_files
    for i in range(args.depth):
        next_target_files =  ["",]
        print("Wave", i + 1, ":\n---")
        for item in target_files:
            new_targets = scan_file(item) # get new targets from text
            if new_targets is None:
                final_files.remove(item)
                continue
            new_targets = [x for x in new_targets if x not in args.exclude] # removing targets if they are to be excluded
            print(new_targets)
            if args.empty:
                new_targets = [x for x in new_targets if (os.stat(x).st_size != 0)] # Remove empty files
            print(new_targets)
            next_target_files = list(set(next_target_files + new_targets)) # joining targets for next iteration with newly found targets and removing duplicate entries
        next_target_files = [os.path.join(args.input_dir, x) for x in next_target_files if x] # appending directory path to the beginning and removing empty entries
        next_target_files = [x for x in next_target_files if x not in final_files] # removing targets for next iteration if they are already present in the final list
        target_files =  next_target_files # Preparing for the next iteration
        for item in target_files: # printing files found in this iteration
            print(item)
        print("---\n")
        final_files = list(set(final_files + target_files)) # adding found files to the final list

    copy_notes(final_files, args.output_dir)
    if args.web:
        final_files = [os.path.basename(x) for x in final_files]
        for filename in final_files:
            with open(os.path.join(args.output_dir, filename), "r+") as file:
                content = webify(file.read(), [x.replace(".md", "") for x in final_files], args.web)
                file.seek(0)
                file.write(content)


if __name__ == "__main__":
    main()
