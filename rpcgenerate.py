#!/usr/bin/env python3

import subprocess
import json
import sys
import os

IDL_TO_JSON_EXECUTABLE = './idl_to_json'


def idlToJson(fileName):

    print(fileName)
    with open(fileName) as idlFile:
        idlText = idlFile.read()
        print(idlText)

    #
    #     Make sure idl_to_json exists and is executable
    #
    if (not os.path.isfile(IDL_TO_JSON_EXECUTABLE)):
        print >> sys.stderr,                                       \
            ("Path %s does not designate a file...run \"make\" to create it" % 
             IDL_TO_JSON_EXECUTABLE)
        raise "No file named " + IDL_TO_JSON_EXECUTABLE
    if (not os.access(IDL_TO_JSON_EXECUTABLE, os.X_OK)):
        print >> sys.stderr, ("File %s exists but is not executable" % 
                              IDL_TO_JSON_EXECUTABLE)
        raise "File " + IDL_TO_JSON_EXECUTABLE + " not executable"

    #
    #     Parse declarations into a Python dictionary
    #
    decls = json.loads(subprocess.check_output([IDL_TO_JSON_EXECUTABLE, fileName]))


    return decls
   

# P
def jsonDictToList(decls):

    functionData = []
    #
    # Loop printing each function signature
    #
    for  name, sig in decls["functions"].iteritems():

        # Python Array of all args (each is a hash with keys "name" and "type")
        args = sig["arguments"]

        # Make a string of form:  "type1 arg1, type2 arg2" for use in function sig
        argstring = ', '.join([a["type"] + ' ' + a["name"] for a in args])

        # print the function signature
        #print "%s %s(%s)" % (sig["return_type"], name, argstring)



        functionData.append((sig["return_type"], name, args))

        print(functionData[0][2][1]["type"] + " " + functionData[0][2][1]["name"])



def createFile(fileName):
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
         
    if len(sys.argv) != 2:
        print("Usage is: ./rpcgenerate [filename]")
        sys.exit()
    fileName = str(sys.argv[1])
    fileProxy = fileName[:-4] + ".proxy.cpp"
    fileStub = fileName[:-4] + ".stub.cpp"

    decls = idlToJson(fileName)
    createFile(fileName)
    jsonDictToList(decls)

