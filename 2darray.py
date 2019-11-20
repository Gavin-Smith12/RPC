#!/usr/bin/env python

### rpcgenerate file takes in an idl file as input and creates proxy and stub
### C++ files which then can be run with expected input to do an RPC call over
### the comp117 network 

import subprocess
import json
import sys
import os

IDL_TO_JSON_EXECUTABLE = './idl_to_json'

### Function takes in an idl file and returns the idl data as JSON data
def idlToJson(fileName):

	with open(fileName) as idlFile:
		idlText = idlFile.read()

	### Make sure the idl file exists and is of the correct format
	if (not os.path.isfile(IDL_TO_JSON_EXECUTABLE)):
		print >> sys.stderr,                                       \
			("Path %s does not designate a file...run \"make\" to create it" % 
			 IDL_TO_JSON_EXECUTABLE)
		raise "No file named " + IDL_TO_JSON_EXECUTABLE
	if (not os.access(IDL_TO_JSON_EXECUTABLE, os.X_OK)):
		print >> sys.stderr, ("File %s exists but is not executable" % 
							  IDL_TO_JSON_EXECUTABLE)
		raise "File " + IDL_TO_JSON_EXECUTABLE + " not executable"

	### Put the declarations into a python dictionary
	decls = json.loads(subprocess.check_output([IDL_TO_JSON_EXECUTABLE, fileName]))


	return decls
   

### Function given to us that creates a list of the arguments of a function
def createFunctionsList(decls):

	functionList = []
	
	### Loop through all function signitures
	for  name, sig in decls["functions"].iteritems():

		### Create array of arguments that contains type and name
		args = sig["arguments"]

		# Make a string of form:  "type1 arg1, type2 arg2" for use in function sig
		argstring = ', '.join([a["type"] + ' ' + a["name"] for a in args])

		functionList.append((sig["return_type"], name, args))

	return functionList

### Returns the list of types of a given dictionary
def createTypesDict(decls):

	return decls["types"]

### Takes in a file name and creates the proxy and stub files, and then writes
### a comment at the top of the files and writes the needed #includes at the 
### top of the files. Writes the files afterwards.
def createFile(fileName):
	fileProxy = fileName[:-4] + ".proxy.cpp"
	fileStub = fileName[:-4] + ".stub.cpp"

	headers = "#include \"rpc%shelper.h\"\n#include\"c150grading.h\"\n" + \
			  "#include <cstdio>\n#include <cstring>\n#include \"c150debug.h\"\n" + \
			  "using namespace C150NETWORK;\nusing namespace std;\n" + \
			  "#include \"%s\"\n\n" 

	proxyComment = "/*\n\tThis file is %s.\n\tWritten by Gavin Smith and Ravi Serota.\n" % fileProxy
	proxyComment += "\tFile sends function names and arguments to server to be computed "
	proxyComment += "and then\n\treturns the value returned by the server.\n*/\n\n" 

	headers = proxyComment + headers

	with open(fileProxy, 'w+') as file:
		file.write(headers % ("proxy", fileName))

	with open(fileStub, 'w+') as file:
		file.write(headers % ("stub", fileName))

### Main function to write the entire proxy file. Takes in a dictionary of the 
### JSON data for the functions and the list of functions needed to be written.
### Parses the JSON data and creates and writes all of the needed functions
### and network calls.
def writeProxy(typeDict, functionList):

	writeString = ""

	### Create declaration line of function
	for func in functionList:
		writeString = createFuncDec(func)

		### Write beginning of file(contains grading/debug statements + readBuffer)
		writeString += writeProxyStart(writeString[:-2], func)

		### Writing function and arguments
		writeString += "\tRPCPROXYSOCKET->write(\"%s\", strlen(\"%s\")+1);\n\n" % (func[1], func[1])
		
		### Convert arguments to strings
		for arg in func[2]:
			ret = createArg(arg, typeDict)
			writeString += ret
		writeString += "\n"

		### Debug statement for invocation then wait
		writeString = writeString + "\tc150debug->printf(C150RPCDEBUG,\"%s: %s() invocation sent, waiting for response\");\n\n" % (fileProxy, func[1])

		### Read from server
		writeString += "\tRPCPROXYSOCKET->read(readBuffer, sizeof(readBuffer));\n\n"

		### Convert return to correct type
		writeString += convertReturnType(func, typeDict)

		### Successful return statement and return
		writeString += "\tc150debug->printf(C150RPCDEBUG,\"%s: %s successful return from remote call\");\n\n" % (fileProxy, func[1])
		### Don't return if void
		if func[0] != "void":
			writeString += "\treturn ret;\n}\n\n"
		else:
			writeString += "}\n\n"

		with open(fileProxy, "a") as file:
			file.write(writeString)

### Function writes boilerplate statements to the beginning of each proxy function
def writeProxyStart(declaredFunc, func):
	### Write grading log
	writeString = "\n\t//\n\t//  DO THIS FIRST OR YOUR ASSIGNMENT WON'T BE GRADED!\n"
	writeString += "\t//\n\n\tGRADEME(argc, argv);\n\n"

	### Grading log for invoking function
	writeString += "\t*GRADING << \"Invoking: %s\" << endl;\n\n" % (declaredFunc)

	### Create read buffer
	if func[0] == "void":
		writeString += "\tchar readBuffer[5];\n\n"
	else:
		writeString += "\tchar readBuffer[512];\n\n"

	### Debug statement for starting write
	writeString += "\tc150debug->printf(C150RPCDEBUG,\"%s: %s() invoked\");\n\n" % (fileProxy, func[1])
	return writeString

### Function creates the function declaration by printing the function type and
### name and then loops through the arguments, printing each.
def createFuncDec(func):
	writeString = "%s %s(" % (func[0], func[1])
	first = True
	### Loop through arguments of the function
	for arg in func[2]:
		typeObj = typeDict[arg["type"]]
		### If its the first argument don't have a comma
		if first:
			if typeObj["type_of_type"] == "array":
				arraySplit = arg["type"].find('[')
				writeString += "%s %s%s" % (arg["type"][:arraySplit][2:], arg["name"], arg["type"][arraySplit:])
			else:
				writeString += "%s %s" % (arg["type"], arg["name"])
			first = False
		else:
			if typeObj["type_of_type"] == "array":
				arraySplit = arg["type"].find('[')
				writeString += ", %s %s%s" % (arg["type"][:arraySplit][2:], arg["name"], arg["type"][arraySplit:])
			else:
				writeString = writeString + ", %s %s" % (arg["type"], arg["name"])
	writeString += ") {\n"
	return writeString

### Function creates a new variable that is of the type of the return type and
### converts what is read from the server to that type.
def convertReturnType(func, typeDict):
	writeString = ""
	if func[0] == "int":
		writeString += intCreateReturn(func[1], "", 0)
	elif func[0] == "float":
		writeString += floatCreateReturn(func[1], "", 0)
	elif func[0] == "string":
		writeString += "string ret = readBuffer;\n"
	elif func[0] == "void":
		writeString += voidCreateReturn(func[1])
	elif typeDict[func[0]]["type_of_type"] == "struct":
		writeString += "\t%s ret;\n" % func[0]
		writeString += structCreateReturn(func[0], func[1], typeDict, "ret")
	return writeString


### Function is called with an argument and the type dictionary and returns 
### the string that is the argument being written to the stub. Calls helper 
### functions to deal with the specific data types.
def createArg(arg, typeDict):
	ret = ""
	if arg["type"] == "int" or arg["type"] == "float":
		ret += numCreateArg(arg["name"])
	elif arg["type"] == "string":
		ret += stringCreateArg(arg["name"])
	elif typeDict[arg["type"]]["type_of_type"] == "array":
		ret += arrayCreateArg(arg["type"], typeDict, arg["name"])
	elif typeDict[arg["type"]]["type_of_type"] == "struct":
		ret += structCreateArg(arg, typeDict, arg["name"])
	else:
		print "Argument is not of known type"
		
	return ret

### Function is given an int or a float and converts it to a string then 
### writes it using the COMP150 network framework.
def numCreateArg(argName):
	writeString = ""
	### If the argument is part of an array take away the brackets as data
	### names cannot have brackets in them.
	nobracketsArgName = argName.replace('[', '').replace(']', '')
	writeString += "\t*GRADING << \"Writing %s with value: \" << %s << endl;\n" % (argName, argName)
	writeString += "\tstring %sStr = to_string(%s);\n" % (nobracketsArgName.replace('.', ''), argName)
	writeString += writeArg(nobracketsArgName)
	writeString += "\n"
	return writeString

### Function takes in a string and then writes the string using the COMP150 network
### framework.
def stringCreateArg(argName):
	writeString = ""
	### If the argument is part of an array take away the brackets as strings
	### cannot have brackets in their name.
	nobracketsArgName = argName.replace('[', '').replace(']', '')
	writeString += "\t*GRADING << \"Writing %s with value: \" << %s << endl;\n" % (argName, argName)
	writeString += "\tstring %sStr = %s;\n" % (nobracketsArgName.replace('.', ''), argName)
	writeString += writeArg(nobracketsArgName)
	writeString += "\n"
	return writeString

### Function takes in an array and loops through the elements, and with each
### element either recursively calls itself or calls one of the other helper
### functions.
def arrayCreateArg(arg, typeDict, name):
	writeString = ""
	typeObj = typeDict[arg]
	if typeObj["type_of_type"] != "builtin":
		memberType = typeObj["member_type"]
	elementCount = int(typeObj["element_count"])
	arrayName = name
	for i in range(elementCount):
		newName = arrayName + "[" + str(i) + "]";
		if memberType == "int" or memberType == "float":
			writeString += numCreateArg(newName)
		elif memberType == "string":
			writeString += stringCreateArg(newName)
		elif typeDict[typeObj["member_type"]]["type_of_type"] == "array":
			writeString += arrayCreateArg(memberType, typeDict, newName)
		elif typeDict[typeObj["member_type"]]["type_of_type"] == "struct":
			structDict = {'type': memberType, 'name': name}
			writeString += structCreateArg(structDict, typeDict, newName)
	return writeString


### Function takes in a struct and loops through the members of the struct 
### and either calls a helper function to have the member written or 
### recursively calls itself if a member is also a struct.
def structCreateArg(arg, typeDict, name):
	writeString = ""
	typeObj = typeDict[arg["type"]]
	structMembers = typeObj["members"]
	structName = name
	for member in structMembers:
		if member["type"] == "int" or member["type"] == "float":
			writeString += numCreateArg(structName + "." + member["name"])
		elif member["type"] == "string":
			writeString += stringCreateArg(structName + "." + member["name"])
		elif typeDict[member["type"]]["type_of_type"] == "array":
			writeString += arrayCreateArg(member["type"], typeDict, structName + "." + member["name"])
		elif typeDict[member["type"]]["type_of_type"] == "struct":
			writeString += structCreateArg(member, typeDict, structName + "." + member["name"])
	return writeString

### Generic function to write the argument to the server.
def writeArg(argName):
	return "\tRPCPROXYSOCKET->write(%sStr.c_str(), %sStr.length()+1);\n" % (argName, argName)

### Function takes in an int name and writes to the C++ a string that reads 
### the string into an int and checks if stoi failed. Iterates how many variables
### have been read (readLen)
def intCreateReturn(funcName, structName, first):
	writeString = ""
	### If not a part of a struct or array the return variable must be declared
	if structName == "":
		writeString += "\tint ret;\n"	
	writeString += "\ttry {\n"
	if structName != "":
		if first:
			writeString += "\t\t%s = stoi(readBuffer);\n\t } catch(invalid_argument& e) {\n" % structName
		else:
			writeString += "\t\t%s = stoi((&(readBuffer[readLen])));\n\t } catch(invalid_argument& e) {\n" % structName
	else:
		if first:
			writeString += "\t\tret = stoi(readBuffer);\n\t } catch(invalid_argument& e) {\n"
		else:
			writeString += "\t\tret = stoi((&(readBuffer[readLen])));\n\t } catch(invalid_argument& e) {\n"
	writeString += "\t\tthrow C150Exception(\"%s: %s received invalid response from the server\");\n\t}\n\n" % (fileProxy, funcName)
	### Write grading log
	if structName == "":
		writeString += "\tGRADING* << \"Returned from %s with \" << ret << endl;\n\n" % (funcName)
	return writeString

### Function takes in a float name and writes to the C++ a string that reads 
### the string into a float and checks if stof failed. Iterates how many variables
### have been read (readLen)
def floatCreateReturn(funcName, structName, first):
	writeString = ""
	### If not a part of a struct or array the return variable must be declared
	if structName == "":
		writeString += "\tfloat ret;\n"
	writeString += "\ttry {\n"
	if structName != "":
		if first:
			writeString += "\t\t%s = stof(readBuffer);\n\t } catch(invalid_argument& e) {\n" % structName
		else:
			writeString += "\t\t%s = stof((&(readBuffer[readLen])));\n\t } catch(invalid_argument& e) {\n" % structName
	else:
		if first:
			writeString += "\t\tret = stof(readBuffer);\n\t } catch(invalid_argument& e) {\n"
		else:
			writeString += "\t\tret = stof((&(readBuffer[readLen])));\n\t } catch(invalid_argument& e) {\n"
	writeString += "\t\tthrow C150Exception(\"%s: %s received invalid response from the server\");\n\t}\n\n" % (fileProxy, funcName)
	### Write grading log
	if structName == "":
		writeString += "\tGRADING* << \"Returned from %s with \" << ret << endl;\n\n" % (funcName)
	return writeString

### Function writes to the C++ file that the function returned but does not 
### declare a return variable.
def voidCreateReturn(funcName):
	writeString = ""
	writeString += "\tGRADING* << \"Returned from %s with void return type\" << endl;\n\n" % (funcName)
	writeString += "\tif (strncmp(readBuffer,\"DONE\", sizeof(readBuffer))!=0) {\n"
	writeString += "\t\tthrow C150Exception(\"%s: %s() received invalid response from the server\");\n\t}\n\n" % (fileProxy, funcName)
	return writeString

### Function takes in a string name and writes the returned string to a return
### variable. Iterates how many variables have been read (readLen)
def stringCreateReturn(funcName, structName, first):
	writeString = ""
	if structName == "":
		writeString += "\tstring ret;\n"
	if structName != "":
		if first:
			writeString += "\t%s = readBuffer;\n" % structName
		else:
			writeString += "\t%s = &(readBuffer[readLen])\n" % structName
	else:
		if first:
			writeString += "\tret = readBuffer;\n"
		else:
			writeString += "\tret = &(readBuffer[readLen])\n"
	if structName == "":
		writeString += "\tGRADING* << \"Returned from %s with \" << ret << endl;\n\n" % (funcName)
	return writeString

### Function takes in an array name and looks in the type dictionary to see
### what type it is, then calls the needed helper function the number of 
### times the array is long. Iterates how many variables have been read from
### the buffer
def arrayCreateReturn(retType, funcName, typeDict, struct):
	writeString = ""
	typeObj = typeDict[retType]
	for i in range(typeObj["element_count"]):
		currentIndex = struct+"["+str(i)+"]"
		if typeObj["member_type"] == "int":
			writeString += intCreateReturn(funcName, currentIndex, first)
			writeString += "\tGRADING* << \"Returned from %s with return \" << %s << endl;\n" % (funcName, currentIndex)
			writeString += "\treadLen += string(%s).length()+1;\n\n" % (currentIndex)
		elif typeObj["member_type"] == "float":
			writeString += floatCreateReturn(funcName, currentIndex, first)
			writeString += "\tGRADING* << \"Returned from %s with return \" << %s << endl;\n" % (funcName, currentIndex)
			writeString += "\treadLen += string(%s).length()+1;\n\n" % (currentIndex)
		elif typeObj["member_type"] == "string":
			writeString += stringCreateReturn(funcName, currentIndex, first)
			writeString += "\tGRADING* << \"Returned from %s with return \" << %s << endl;\n" % (funcName, currentIndex)
			writeString += "\treadLen += %s.length()+1;\n\n" % (currentIndex)
		elif typeDict[typeObj["member_type"]]["type_of_type"] == "array":
			writeString += arrayCreateReturn(typeObj["member_type"], funcName, typeDict, currentIndex)
		elif typeDict[typeObj["member_type"]]["type_of_type"] == "struct":
			writeString += structCreateReturn(typeObj["member_type"], funcName, typeDict, currentIndex)
	return writeString

### Function takes in a struct argument and looks in the type dictionary to see
### what the member types are, then loops through the members to call the 
### needed helper function. Iterates readLen every time a variable is read.
def structCreateReturn(retType, funcName, typeDict, struct):
	writeString = ""
	typeObj = typeDict[retType]
	structMembers = typeObj["members"]
	for member in structMembers:
		if member["type"] == "int":
			writeString += intCreateReturn(funcName, struct+"."+member["name"], first)
			writeString += "\tGRADING* << \"Returned from %s with return \" << %s << endl;\n" % (funcName, struct+"."+member["name"])
			writeString += "\treadLen += string(%s).length()+1;\n\n" % (struct+"."+member["name"])
			first = False
		elif member["type"] == "float":
			writeString += floatCreateReturn(funcName, struct+"."+member["name"], first)
			writeString += "\tGRADING* << \"Returned from %s with return \" << %s << endl;\n" % (funcName, struct+"."+member["name"])
			writeString += "\treadLen += string(%s).length()+1;\n\n" % (struct+"."+member["name"])
			first = False
		elif member["type"] == "string":
			writeString += stringCreateReturn(funcName, struct + "." + member["name"], first)
			writeString += "\tGRADING* << \"Returned from %s with return \" << %s << endl;\n" % (funcName, struct+"."+member["name"])
			writeString += "\treadLen += %s.length()+1;\n\n" % (struct+"."+member["name"])
			first = False
		elif typeDict[member["type"]]["type_of_type"] == "array":
			writeString += arrayCreateReturn(member["type"], funcName, typeDict, struct + "." + member["name"])
		elif typeDict[member["type"]]["type_of_type"] == "struct":
			writeString += structCreateReturn(member["type"], funcName, typeDict, struct + "." + member["name"])
	return writeString

def writeStub(typeDict, functionList):

	writeString = ""

	### Create declaration for function stub
	for func in functionList:
		writeString = "void __%s(" % func[1]
		writeString += ") {\n"

		### Create read buffer
		if func[0] == "void":
			writeString += "\tchar doneBuffer[5] = \"DONE\";\n\n"
		
		if len(func[2]) > 0:
			writeString += "\tchar readBuffer[512];\n\n"

		for arg in func[2]:
			if typeDict[arg["type"]]["type_of_type"] == "array":
				writeString += "\tstring temp;\n"
				break

		### Declare argument variables
		for arg in func[2]:
			writeString += stubCreateArg(arg, typeDict)


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
			typeString = arg["type"]
			name = arg["name"]
			if typeString == "int":
				# ret is tuple (string, bool)
				ret = intToArgType(name, first)
				writeString += ret[0]
				first = ret[1]
			elif typeString == "float":
				ret = floatToArgType(name, first)
				writeString += ret[0]
				first = ret[1]
			elif typeString == "string":
				ret = stringToArgType(name, first)
				writeString += ret[0]
				first = ret[1]
			elif typeDict[typeString]["type_of_type"] == "array":
				ret = arrayToArgType(first, arg, typeDict)
				writeString += ret[0]
				first = ret[1]

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
		file.write(writeSupportFuncs(functionList))

def writeSupportFuncs(functionList):
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
	for func in functionList:
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

def stubCreateArg(arg, typeDict):
	writeString = ""
	typeOfType = typeDict[arg["type"]]["type_of_type"]
	if typeOfType == "builtin":
		writeString += "\t%s %s;\n" % (arg["type"], arg["name"])
	elif typeOfType == "array":
		memberType = typeDict[arg["type"]]["member_type"]
		elementCount = typeDict[arg["type"]]["element_count"]
		writeString += "\t%s %s[%s];\n" % (memberType, arg["name"], str(elementCount))
	elif typeOfType == "struct":
		pass
	return writeString

def arrayToArgType(first, arg, typeDict):
	if first:
		first = False

	writeString = ""
	typeObj = typeDict[arg["type"]]
	memberType = typeObj["member_type"]

	writeString += "\tfor (int i=0; i<%s; i++) {\n" % typeObj["element_count"]
	writeString += "\t\ttemp = string(&readBuffer[readLen]);\n"

	if memberType == "int" or memberType == "float":
		writeString += "\t\ttry {\n" 
		if memberType == "int":
			writeString += "\t\t\t%s[i] = stoi(temp);\n" % arg["name"]
			writeString += "\t\t} catch (invalid_argument&) {\n"
			writeString += "\t\t\tcerr << \"Problem with stoi'ing\" << endl;\n"
		else:
			writeString += "\t\t\t%s[i] = stof(temp);\n" % arg["name"]
			writeString += "\t\t} catch (invalid_argument&) {\n"
			writeString += "\t\t\tcerr << \"Problem with stof'ing\" << endl;\n"
		writeString += "\t\t}\n"
	elif memberType == "string":
		writeString += "\t\t%s[i] = temp;\n" % arg["name"]
	
	writeString += "\t\treadLen += temp.length()+1;\n"
	writeString += "\t}\n"
	first = False

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
	functionList = createFunctionsList(decls)
	typeDict = createTypesDict(decls)
	writeProxy(typeDict, functionList)
	writeStub(typeDict, functionList)
