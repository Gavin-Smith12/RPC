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

    headers = "#include \"rpc%shelper.h\"\n" + \
              "#include <cstdio>\n#include <cstring>\n#include \"c150debug.h\"\n" + \
              "using namespace C150NETWORK;\nusing namespace std;\n" + \
              "#include \"%s\"\n\n" 

    with open(fileProxy, 'w+') as file:
        file.write(headers % ("proxy", fileName))

    with open(fileStub, 'w+') as file:
        file.write(headers % ("stub", fileName))



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
        if func[0] == "void":
            writeString += "\tchar readBuffer[5];\n\n"
        else:
            writeString = writeString + "\tchar readBuffer[512];\n\n"

        ### Convert arguments to strings
        for arg in func[2]:
            if arg["type"] == "int" or arg["type"] == "float":
                writeString += numCreateArg(arg["name"])
            elif arg["type"] == "string":
                writeString += stringCreateArg(arg["name"])

        writeString = writeString + "\n"

        ### Debug statement for starting write
        writeString = writeString + "\tc150debug->printf(C150RPCDEBUG,\"%s: %s() invoked\");\n\n" % (fileProxy, func[1])

        ### Writing function and arguments
        writeString = writeString + "\tRPCPROXYSOCKET->write(\"%s\", strlen(\"%s\")+1);\n" % (func[1], func[1])
        for arg in func[2]:
            writeString += writeArg(arg["name"])

        writeString += "\n"

        ### Debug statement for invocation then wait
        writeString = writeString + "\tc150debug->printf(C150RPCDEBUG,\"%s: %s() invocation sent, waiting for response\");\n\n" % (fileProxy, func[1])

        ### Read from server
        writeString += "\tRPCPROXYSOCKET->read(readBuffer, sizeof(readBuffer));\n\n"

        ### Convert return to correct type
        if func[0] == "int":
            writeString += intCreateReturn(func[1])
        elif func[0] == "float":
            writeString += floatCreateReturn(func[1])
        elif func[0] == "string":
            writeString += "string ret = readBuffer;\n"
        elif func[0] == "void":
            writeString += voidCreateReturn(func[1])

        ### Successful return statement and return
        writeString += "\tc150debug->printf(C150RPCDEBUG,\"%s: %s successful return from remote call\");\n\n" % (fileProxy, func[1])
        ### Don't return if void
        if func[0] != "void":
            writeString += "\treturn ret;\n}\n\n"
        else:
            writeString += "}\n\n"

        with open(fileProxy, "a") as file:
            file.write(writeString)


def numCreateArg(argName):
    return "\tstring %sStr = to_string(%s);\n" % (argName, argName)

def stringCreateArg(argName):
    return "\t string %sStr = %s;\n" % (argName, argName)

def writeArg(argName):
    return "\tRPCPROXYSOCKET->write(%sStr.c_str(), %sStr.length()+1);\n" % (argName, argName)

def intCreateReturn(funcName):
    writeString = ""
    writeString += "\tint ret;\n"
    writeString += "\ttry {\n"
    writeString += "\t\tret = stoi(readBuffer);\n\t } catch(invalid_argument& e) {\n"
    writeString += "\t\tthrow C150Exception(\"%s: %s received invalid response from the server\");\n\t}\n\n" % (fileProxy, funcName)
    return writeString

def floatCreateReturn(funcName):
    writeString = ""
    writeString += "\tfloat ret;\n"
    writeString += "\ttry {\n"
    writeString += "\t\tret = stof(readBuffer);\n\t } catch(invalid_argument& e) {\n"
    writeString += "\t\tthrow C150Exception(\"%s: %s received invalid response from the server\");\n\t}\n\n" % (fileProxy, funcName)
    return writeString

def voidCreateReturn(funcName):
    writeString = ""
    writeString += "\tif (strncmp(readBuffer,\"DONE\", sizeof(readBuffer))!=0) {\n"
    writeString += "\t\tthrow C150Exception(\"%s: %s() received invalid response from the server\");\n\t}\n\n" % (fileProxy, funcName)
    return writeString

def writeStub(functionData):

    writeString = ""

    ### Create declaration for function stub
    for func in functionData:
        writeString = "void __%s(" % func[1]
        writeString += ") {\n"

        ### Create read buffer
        if func[0] == "void":
            writeString += "\tchar doneBuffer[5] = \"DONE\";\n\n"
        
        if len(func[2]) > 0:
            writeString += "\tchar readBuffer[512];\n\n"

        ### Declare argument variables
        for arg in func[2]:
            writeString += "\t%s %s;\n" % (arg["type"], arg["name"])

        ### Declare return variable
        if func[0] != "void":
            writeString += "\t%s ret;\n" % (func[0])

        ### Declare length variable for parsing readBuffer
        if len(func[2]) > 0:
            writeString += "\tint readLen = 0;\n"

        writeString += "\n"
        writeString += "\t//\n\t// Time to actually call the function\n\t//\n"

        writeString += "\tc150debug->printf(C150RPCDEBUG,\"%s: invoking %s()\");\n" % (fileProxy, func[1])

        writeString += "\tusleep(250000);\n"

        if len(func[2]) > 0:
            writeString += "\tRPCSTUBSOCKET->read(readBuffer, sizeof(readBuffer));\n\n"


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
                ret = floatToArgType(name, first)
                writeString += ret[0]
                first = ret[1]
            elif type == "string":
                ret = stringToArgType(name, first)
                writeString += ret[0]
                first = ret[1]
            elif type == "array":
                pass
            elif type == "struct":
                pass

        firstArg = True
        if func[0] == "void":
            writeString += "\t%s(" % (func[1])
        else:
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
        elif func[0] == "string":
            writeString += "\tstring retStr = ret;\n"
        else:
            pass

        writeString += "\tc150debug->printf(C150RPCDEBUG,\"%s: returned from %s() -- responding to client\");\n" % (fileStub, func[1])

        if func[0] == "void":
            writeString += "\tRPCSTUBSOCKET->write(doneBuffer, strlen(doneBuffer)+1);\n"
        else: 
            writeString += "\tRPCSTUBSOCKET->write(retStr.c_str(), retStr.length()+1);\n"
        writeString += "}\n\n"


        with open(fileStub, "a") as file:
            file.write(writeString)

    with open(fileStub, "a") as file:
        file.write(writeSupportFuncs(functionData))

def writeSupportFuncs(functionData):
    writeString = "void getFunctionNamefromStream();\n\n"
    writeString += "void __badFunction(char *functionName) {\n"
    writeString += "\tchar doneBuffer[5] = \"BAD\";\n"
    writeString += "\tc150debug->printf(C150RPCDEBUG,\"%s: received call for nonexistent function %%s()\",functionName);\n" % fileStub
    writeString += "\tRPCSTUBSOCKET->write(doneBuffer, strlen(doneBuffer)+1);\n}\n\n"
    writeString += "void getFunctionNameFromStream(char *buffer, unsigned int bufSize);\n\n"
    writeString += "void dispatchFunction() {\n\n"
    writeString += "\tchar functionNameBuffer[50];\n"
    writeString += "\tgetFunctionNameFromStream(functionNameBuffer,sizeof(functionNameBuffer));\n"
    writeString += "\tif(!RPCSTUBSOCKET->eof()) {\n"
    first = True
    for func in functionData:
        if first:
            writeString += "\t\tif (strcmp(functionNameBuffer, \"%s\") == 0)\n\t\t\t__%s();\n" % (func[1], func[1])
            first = False
        else:
            writeString += "\t\telse if (strcmp(functionNameBuffer, \"%s\") == 0)\n\t\t\t__%s();\n" % (func[1], func[1])
    writeString += "\t\telse\n\t\t\t__badFunction(functionNameBuffer);\n\t}\n}\n\n"
    writeString += "void getFunctionNameFromStream(char *buffer, unsigned int bufSize) {\n"
    writeString += "\tunsigned int i;\n\tchar *bufp;\n\tbool readnull;\n\tssize_t readlen;\n"
    writeString += "\treadnull = false;\n\tbufp = buffer;\n"
    writeString += "\tfor (i=0; i< bufSize; i++) {\n"
    writeString += "\t\treadlen = RPCSTUBSOCKET->read(bufp, 1);\n"
    writeString += "\t\tif (readlen == 0) {\n\t\t\tbreak;\n\t\t}\n"
    writeString += "\t\tif(*bufp++ == \'\\0\') {\n\t\t\treadnull = true;\n\t\t\tbreak;\n\t\t}\n\t}\n"
    writeString += "\tif (readlen == 0) {\n"
    writeString += "\t\tc150debug->printf(C150RPCDEBUG,\"%s: read zero length message, checking EOF\");\n" % fileStub[:-4]
    writeString += "\t\tif(RPCSTUBSOCKET->eof()) {\n"
    writeString += "\t\t\tc150debug->printf(C150RPCDEBUG,\"%s: EOF signaled on input\");\n" % fileStub[:-4]
    writeString += "\t\t} else {\n"
    writeString += "\t\t\tthrow C150Exception(\"%s: unexpected zero length read without eof\");\n\t\t}\n\t}\n" % fileStub[:-4]
    writeString += "\telse if(!readnull)\n"
    writeString += "\t\tthrow C150Exception(\"%s: method name not null terminated or too long\");\n}" % fileStub[:-4]
    return writeString

def intToArgType(argName, first):
    writeString = ""
    if first:
        writeString += "\t%s = stoi(string(readBuffer));\n" % (argName)
        writeString += "\treadLen += to_string(%s).length()+1;\n" % (argName)
        first = False
    else:
        writeString += "\t%s = stoi(string(&(readBuffer[readLen])));\n" % (argName)
        writeString += "\treadLen += to_string(%s).length()+1;\n" % (argName)
    return (writeString, first)

def floatToArgType(argName, first):
    writeString = ""
    if first:
        writeString += "\t%s = stof(string(readBuffer));\n" % (argName)
        writeString += "\treadLen += to_string(%s).length()+1;\n" % (argName)
        first = False
    else:
        writeString += "\t%s = stof(string(&(readBuffer[readLen])));\n" % (argName)
        writeString += "\treadLen += to_string(%s).length()+1;\n" % (argName)
    return (writeString, first)

def stringToArgType(argName, first):
    writeString = ""
    if first:
        writeString += "\t%s = readBuffer;\n" % (argName)
        writeString += "\treadLen += %s.length()+1;\n" % (argName)
        first = False
    else:
        writeString += "\t%s = &(readBuffer[readLen]);\n" % (argName)
        writeString += "\treadLen += %s.length()+1;\n" % (argName)
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


