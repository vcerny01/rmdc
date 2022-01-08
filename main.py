#!/usr/bin/env python3

#
# Name: roamshare
# Author: Vít Černý
# License: GPL v3
# Description: Intelligent sharing exported markdown from Roam
#
# -*- coding: utf-8 -*-

import argparse
import re
import os
import shutil

LINK_PATTERN = re.compile("\[\[(.*?)\]\]")

def parse_args():
    "Parse and return command line arguments"
    parser = argparse.ArgumentParser(description="Share your markdown notes in context. Go to the folder with your notes and run this program")
    parser.add_argument("-f", "--file", type=str, help="Target filename", required=True)
    parser.add_argument("-d", "--depth", type=int, help="Depth of recursion", required=True)
    parser.add_argument("-i", "--input-dir", type=str, help="Path to input directory with your notes")
    parser.add_argument("-o", "--output-dir", type=str, help="Path to output directory", required=True)
    return parser.parse_args()


def scan_file(filename, dir):
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


def main():
    args = parse_args()
    if (args.input_dir[len(args.input_dir) - 1] != '/'):
        args.input_dir += '/'
    print("Starting with note:", args.file, "\n")

    final_files = [args.input_dir + args.file]
    target_files = final_files
    for i in range(args.depth):
        next_target_files =  ["",]
        print("Wave", i + 1, ":\n---")
        for item in target_files:
            new_targets = scan_file(item, args.input_dir)
            if new_targets == None:
                final_files.remove(item)
                continue
            next_target_files = list(set(next_target_files + new_targets)) # joining targets and removing duplicate entries
            next_target_files[:] = [x for x in next_target_files if x]
        target_files =  [args.input_dir + x for x in next_target_files]
        for item in target_files:
            print(item)
        print("---")
        final_files += target_files
    copy_notes(final_files, args.output_dir)


if __name__ == "__main__":
    main()
