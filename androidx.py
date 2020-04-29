# author: haodongyuan
# date: 2019/3/8
# description: 用来迁移到AndroidX
# python3

from pathlib import Path
import csv
import os

import argparse


def main():
        
    parser = argparse.ArgumentParser(
        description='androidx migration helper')
    parser.add_argument('--mappingClass', dest='mappingClass',
                        help='csv mapping file path. you can get this file from https://developer.android.com/topic/libraries/support-library/downloads/androidx-class-mapping.csv')
    parser.add_argument('--mappingArtifact', dest='mappingArtifact',
                        help='csv mapping file path. you can get this file from https://developer.android.com/topic/libraries/support-library/downloads/androidx-artifact-mapping.csv')


    parser.add_argument('--dir', dest='rootDir', help='search root dir')
    parser.add_argument('--check', help='check only. no modification')
    parser.add_argument('--mode', dest='mode',
                        help='"sx" support -> androidx, "xs" androidx -> support')

    args = parser.parse_args()


    if (args.mappingClass is None):
        print("class mapping file must be provided. see help.")
        exit(-1)
    if (args.mappingArtifact is None):
        print("artifact mapping file must be provided. see help.")
        exit(-1)
    
    mapping = {}
    reverseMapping = {}
    with open(args.mappingClass) as fh:
        rd = csv.DictReader(fh, delimiter=',')
        for row in rd:
            support = row['Support Library class']
            androidx = row['Android X class']
            if (support is None):
                print(
                    "invalid mapping file. column with 'Support Library class' must be set")
            if (androidx is None):
                print("invalid mapping file. column with 'Android X class' must be set")
            if support != androidx:
                mapping[support] = androidx
                reverseMapping[androidx] = support
            pass

    with open(args.mappingArtifact) as fh:
        rd = csv.DictReader(fh, delimiter=',')
        for row in rd:
            support = row['Old build artifact']
            androidx = row['AndroidX build artifact']
            if (support is None):
                print(
                    "invalid mapping file. column with 'Old build artifact' must be set")
            if (androidx is None):
                print("invalid mapping file. column with 'AndroidX build artifact' must be set")
            if support != androidx:
                mapping[support] = androidx
                reverseMapping[androidx] = support
            pass
    

    print("listing {}".format(args.rootDir))
    
    # 指定文件后缀
    files = []
    for ext in ["java", "kt", "xml", "pro", "gradle"]:
        files += list(Path(args.rootDir).rglob(getPathMatch(ext)))


    # 过滤掉build目录下的文件
    files = list(filter(lambda f: len(f.suffix) > 0, files))
    files = list(filter(lambda f: 'build' not in f.parts, files))
    files = list(filter(lambda f: '.idea' not in f.parts, files))
    files = list(filter(lambda f: '.git' not in f.parts, files))
    print("total files: {}".format(len(files)))


    if (args.check):
        if args.mode == "sx":
            check(files, mapping)
        elif args.mode == "xs":
            check(files, reverseMapping)
        else:
            print("unknown mode")
            exit(-1)
    else:
        if args.mode == "sx":
            replace(files, mapping)
        elif args.mode == "xs":
            replace(files, reverseMapping)
        else:
            print("unknown mode")
            exit(-1)

def getPathMatch(str):
    out = "*."
    for c in str:
        out += "["
        out += c
        out += c.upper()
        out += "]"
    return out
    
def check(files, mapping):
    print("checking...")
    for f in files:
        with open(f, "rt") as fin:
            lineNumber = 0
            for line in fin:
                lineNumber = lineNumber + 1
                mapped = getMapped(mapping, line)
                if (mapped != None):
                    print(("[{}] contains \'{}\', which should be \'{}\' (line {})").format(
                        f, mapped[0], mapped[1], lineNumber))
                    exit(-1)
    print("congratulations. all files are passed.")


def replace(files, mapping):
    if (input("Make sure you have a backup of this project? [y/n] ") not in ["y", "yes"]):
        print("Plase make a backup first.")
        exit(-2)
    if (input("The author of this script is not responsable of any problems caused by using this script. agreed? [y/n] ") not in ["y", "yes"]):
        print("You can use '--check' to do the checking instead, which will not modify the project files.")
        exit(-2)

    print("replacing...")
    total = len(files)
    step = total / 100
    processedCount = 0
    count = 0
    updatedFiles = []
    for f in files:
        with open(f, "rt") as fin:
            
            processedCount += 1
            count += 1
            if(count >= step):
                print("progressing... {}/{}".format(processedCount, total))
                count = 0
        
            lines = []
            needUpdateFile = False
            for line in fin:
                mapped = getMapped(mapping, line)
                if (mapped != None):
                    line = line.replace(mapped[0], mapped[1])
                    needUpdateFile = True
                lines.append(line)
            if (needUpdateFile):
                with open(f, "wt") as fout:
                    fout.write("".join(lines))
                    updatedFiles.append(f)

    if(len(updatedFiles) == 0):
        print("congratulations. all files are passed")
    else:
        print("{} files updated. files: {}".format(len(updatedFiles), "\n".join(str(f) for f in updatedFiles)))


def getMapped(mapping, str):
    for key, value in mapping.items():
        if (key in str):
            return (key, value)
    return None


main()

print("Here are some steps you might take afterwards:")
print("1. Find proper version for androidx or android support modules. Same modules have different version between Androidx and support")
print("2. Compile source code and fix errors (which are mostly nullability checks)")
print("3. Buy me a bear :)")
