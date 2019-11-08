#!/usr/bin/python3

import sys
import argparse

def main(argv):
    if len(sys.argv) != 2:
        print("Usage is: ./rpcgenerage [filename]")
        sys.exit()
    fileName = str(sys.argv[1])
    fileProxy = fileName[:-4] + ".proxy.cpp"
    fileStub = fileName[:-4] + ".stub.cpp"

    headers = "#include \"%s\"\n#include \"rpc%shelper.h\"\n" + \
              "#include <cstdio>\n#include <cstring>\n#include \"c150debug.h\"\n" + \
              "using namespace C150NETWORK;\n"

    file = open(fileProxy, 'w+')
    file.write(headers % (fileName, "proxy"))
    file.close()

    file = open(fileStub, 'w+')
    file.write(headers % (fileName, "stub"))
    file.close()

if __name__ == "__main__":
    main(sys.argv[1:])