#!/usr/bin/env python3

import subprocess
import json
import sys
import os

IDL_TO_JSON_EXECUTABLE = './idl_to_json'


def idlToJson(fileName):

    with open(fileName) as idlFile:
        idlText = idlFile.read()

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

    return functionData



def createFile(fileName):
    fileProxy = fileName[:-4] + ".proxy.cpp"
    fileStub = fileName[:-4] + ".stub.cpp"

    headers = "#include \"%s\"\n#include \"rpc%shelper.h\"\n" + \
              "#include <cstdio>\n#include <cstring>\n#include \"c150debug.h\"\n" + \
              "using namespace C150NETWORK;\n"

    with open(fileProxy, 'w+') as file:
        file.write(headers % (fileName, "proxy"))

    with open(fileStub, 'w+') as file:
        file.write(headers % (fileName, "stub"))



def writeProxy(functionData):

    writeString = ""

    ### Create declaration line of function
    for func in functionData:
        writeString = "%s %s(" % (func[0], func[1])
        first = True
        for arg in func[2]:
            if first:
                writeString = writeString + "%s %s" % (arg["type"], arg["name"])
                first = False
            else:
                writeString = writeString + ", %s %s" % (arg["type"], arg["name"])
        writeString = writeString + ") {\n"

        ### Create read buffer
        writeString = writeString + "\tchar readBuffer[512];\n\n"

        ### Convert arguments to strings
        for arg in func[2]:
            if arg["type"] == "int" or arg["type"] == "float":
                writeString += numCreateArg(arg["name"])

        writeString = writeString + "\n"

        ### Debug statement for starting write
        writeString = writeString + "\tc150debug->printf(C150RPCDEBUG,\"%s: %s() invoked\");\n\n" % (fileProxy, func[1])

        ### Writing function and arguments
        writeString = writeString + "\tRPCPROXYSOCKET->write(\"%s\", strlen(\"%s\")+1);\n" % (func[1], func[1])
        for arg in func[2]:
            if arg["type"] == "int" or arg["type"] == "float":
                writeString += numWriteArg(arg["name"])

        writeString += "\n"

        ### Debug statement for invocation then wait
        writeString = writeString + "\tc150debug->printf(C150RPCDEBUG,\"%s: %s() invocation sent, waiting for response\");\n\n" % (fileProxy, func[1])

        ### Read from server
        writeString += "\tRPCPROXYSOCKET->read(readBuffer, sizeof(readBuffer));\n\n"

        ### Convert return to correct type
        if func[0] == "int":
            writeString += intCreateReturn(func[1])

        ### Successful return statement and return
        writeString += "\tc150debug->printf(C150RPCDEBUG,\"%s: %s successful return from remote call\");\n\n" % (fileProxy, func[1])
        writeString += "\treturn ret;\n}\n\n"

        with open(fileProxy, "a") as file:
            file.write(writeString)


def numCreateArg(argName):
    return "\tstring %sStr = to_string(%s);\n" % (argName, argName)

def numWriteArg(argName):
    return "\tRPCPROXYSOCKET->write(%sStr.c_str(), %sStr.length()+1);\n" % (argName, argName)

def intCreateReturn(funcName):
    writeString = ""
    writeString += "\tint ret;\n"
    writeString += "\ttry {\n"
    writeString += "\t\tret = stoi(readBuffer);\n\t } catch(invalid_argument& e) {\n"
    writeString += "\t\tthrow C150Exception(\"%s: %s received invalid response from the server\");\n\t}\n\n" % (fileProxy, funcName)
    return writeString


def writeStub(functionData):

    writeString = ""

    ### Create declaration for function stub
    for func in functionData:
        writeString += "__%s %s(" % (func[0], func[1])
        first = True

        for arg in func[2]:
            if first:
                writeString += writeString + "%s %s" % (arg["type"], arg["name"])
                first = False
            else:
                writeString += writeString + ", %s %s" % (arg["type"], arg["name"])
        writeString += writeString + ") {\n"

        ### Create read buffer
        writeString += writeString + "\tchar readBuffer[512];\n\n"

        ### Declare argument variables
        for arg in func[2]:
            writeString += "\t%s %s;\n" % (arg["type"], arg["name"])

        ### Declare return variable
        writeString += "\t%s ret;\n" % (func[0])

        ### Declare length variable for parsing readBuffer
        writeString += "\tint readLen = 0;\n"

        writeString += writeString + "\n"
        writeString += "\t//\n\t// Time to actually call the function\n\t//\n"

        writeString += "\tc150debug->printf(C150RPCDEBUG,\"%s: invoking %s()\");" % (fileProxy, func[1])

        writeString += "RPCSTUBSOCKET->read(readBuffer, sizeof(readBuffer));\n\n"


        ### Loop through arguments
        first = True;
        for arg in func[2]:
            type = arg["type"]
            name = arg["name"]
            if type == "int":
                # ret is tuple (string, bool)
                ret = intToArgType(name, first)
                writeString += ret[0]
                first = ret[1]

            elif type == "float":
                pass
            elif type == "string":
                pass
            elif type == "array":
                pass
            elif type == "struct":
                pass

        firstArg = True
        writeString += "\tret = %s(" % (func[1])
        for arg in func[2]:
            if firstArg:
                writeString = writeString + "%s" % (arg["name"])
                firstArg = False
            else:
                writeString = writeString + ", %s" % (arg["name"])
        writeString = writeString + ");\n"



        if func[0] == "int" or func[0] == "float":
            writeString += "\tstring retStr = to_string(ret);\n"
        else:
            ### TODO ###
            pass

        writeString += "\tc150debug->printf(C150RPCDEBUG,\"%s: returned from %s() -- responding to client\");\n" % (fileStub, func[1])

        writeString += "\tRPCSTUBSOCKET->write(retStr.c_str(), retStr.length()+1);\n"
        writeString += "}\n"

    with open(fileStub, "a") as file:
            file.write(writeString)

def intToArgType(argName, first):
    writeString = ""
    if first:
        writeString += "\t%s = stoi(string(readBuffer));\n" % (argName)
        writeString += "\treadLen += to_string(%s).length();\n" % (argName)
        first = False
    else:
        writeString += "\t%s = stoi(string(&(readBuffer[readLen+1])));\n" % (argName)
    return (writeString, first)

if __name__ == "__main__":
         
    if len(sys.argv) != 2:
        print("Usage is: ./rpcgenerate [filename]")
        sys.exit()
    fileName = str(sys.argv[1])
    fileProxy = fileName[:-4] + ".proxy.cpp"
    fileStub = fileName[:-4] + ".stub.cpp"

    decls = idlToJson(fileName)
    createFile(fileName)
    functionData = jsonDictToList(decls)
    writeProxy(functionData)
    writeStub(functionData)


