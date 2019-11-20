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

	stubComment = "/*\n\tThis file is %s.\n\tWritten by Gavin Smith and Ravi Serota.\n" % fileStub
	stubComment += "\tFile takes in functions and arguments and gives them to the cpp file"
	stubComment += "to be\ncomputed and then returns the result to the client.\n*/\n\n" 

	with open(fileProxy, 'w+') as file:
		file.write(proxyComment+headers % ("proxy", fileName))

	with open(fileStub, 'w+') as file:
		file.write(stubComment+headers % ("stub", fileName))

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
		writeString += "\tc150debug->printf(C150RPCDEBUG,\"%s: %s() invocation sent, waiting for response\");\n\n" % (fileProxy, func[1])

		### Wait for the server to send all messages
		writeString += "\tusleep(500000);\n\n"

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
	#writeString = "\n\t//\n\t//  DO THIS FIRST OR YOUR ASSIGNMENT WON'T BE GRADED!\n"
	#writeString += "\t//\n\n\tGRADEME(argc, argv);\n\n"

	### Grading log for invoking function
	#writeString += "\t*GRADING << \"Invoking: %s\" << endl;\n\n" % (declaredFunc)
	writeString = ""
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
	first = False
	if func[0] != "void":
		writeString += "\tint readLen = 0;\n\n"
	if func[0] == "int":
		writeString += intCreateReturn(func[1], "", first)
	elif func[0] == "float":
		writeString += floatCreateReturn(func[1], "", first)
	elif func[0] == "string":
		writeString += "string ret = readBuffer;\n"
	elif func[0] == "void":
		writeString += voidCreateReturn(func[1])
	elif typeDict[func[0]]["type_of_type"] == "struct":
		writeString += "\t%s ret;\n" % func[0]
		writeString += structCreateReturn(func[0], func[1], typeDict, "ret", first)
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
	#writeString += "\t*GRADING << \"Writing %s with value: \" << %s << endl;\n" % (argName, argName)
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
	#writeString += "\t*GRADING << \"Writing %s with value: \" << %s << endl;\n" % (argName, argName)
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
	argName = argName.replace('.', '')
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
	#if structName == "":
		#writeString += "\tGRADING* << \"Returned from %s with \" << ret << endl;\n\n" % (funcName)
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
	#if structName == "":
		#writeString += "\tGRADING* << \"Returned from %s with \" << ret << endl;\n\n" % (funcName)
	return writeString

### Function writes to the C++ file that the function returned but does not 
### declare a return variable.
def voidCreateReturn(funcName):
	writeString = ""
	#writeString += "\tGRADING* << \"Returned from %s with void return type\" << endl;\n\n" % (funcName)
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
			writeString += "\t%s = &(readBuffer[readLen]);\n" % structName
	else:
		if first:
			writeString += "\tret = readBuffer;\n"
		else:
			writeString += "\tret = &(readBuffer[readLen]);\n"
	#if structName == "":
		#writeString += "\tGRADING* << \"Returned from %s with \" << ret << endl;\n\n" % (funcName)
	return writeString

### Function takes in an array name and looks in the type dictionary to see
### what type it is, then calls the needed helper function the number of 
### times the array is long. Iterates how many variables have been read from
### the buffer
def arrayCreateReturn(retType, funcName, typeDict, struct, first):
	writeString = ""
	typeObj = typeDict[retType]
	for i in range(typeObj["element_count"]):
		currentIndex = struct+"["+str(i)+"]"
		if typeObj["member_type"] == "int":
			writeString += intCreateReturn(funcName, currentIndex, first)
			#writeString += "\tGRADING* << \"Returned from %s with return \" << %s << endl;\n" % (funcName, currentIndex)
			writeString += "\treadLen += string(%s).length()+1;\n\n" % (currentIndex)
			first = False
		elif typeObj["member_type"] == "float":
			writeString += floatCreateReturn(funcName, currentIndex, first)
			#writeString += "\tGRADING* << \"Returned from %s with return \" << %s << endl;\n" % (funcName, currentIndex)
			writeString += "\treadLen += string(%s).length()+1;\n\n" % (currentIndex)
			first = False
		elif typeObj["member_type"] == "string":
			writeString += stringCreateReturn(funcName, currentIndex, first)
			#writeString += "\tGRADING* << \"Returned from %s with return \" << %s << endl;\n" % (funcName, currentIndex)
			writeString += "\treadLen += %s.length()+1;\n\n" % (currentIndex)
			first = False
		elif typeDict[typeObj["member_type"]]["type_of_type"] == "array":
			writeString += arrayCreateReturn(typeObj["member_type"], funcName, typeDict, currentIndex, first)
		elif typeDict[typeObj["member_type"]]["type_of_type"] == "struct":
			writeString += structCreateReturn(typeObj["member_type"], funcName, typeDict, currentIndex, first)
	return writeString

### Function takes in a struct argument and looks in the type dictionary to see
### what the member types are, then loops through the members to call the 
### needed helper function. Iterates readLen every time a variable is read.
def structCreateReturn(retType, funcName, typeDict, struct, first):
	writeString = ""
	typeObj = typeDict[retType]
	structMembers = typeObj["members"]
	for member in structMembers:
		if member["type"] == "int":
			writeString += intCreateReturn(funcName, struct+"."+member["name"], first)
			#writeString += "\tGRADING* << \"Returned from %s with return \" << %s << endl;\n" % (funcName, struct+"."+member["name"])
			writeString += "\treadLen += string(%s).length()+1;\n\n" % (struct+"."+member["name"])
			first = False
		elif member["type"] == "float":
			writeString += floatCreateReturn(funcName, struct+"."+member["name"], first)
			#writeString += "\tGRADING* << \"Returned from %s with return \" << %s << endl;\n" % (funcName, struct+"."+member["name"])
			writeString += "\treadLen += string(%s).length()+1;\n\n" % (struct+"."+member["name"])
			first = False
		elif member["type"] == "string":
			writeString += stringCreateReturn(funcName, struct + "." + member["name"], first)
			#writeString += "\tGRADING* << \"Returned from %s with return \" << %s << endl;\n" % (funcName, struct+"."+member["name"])
			writeString += "\treadLen += %s.length()+1;\n\n" % (struct+"."+member["name"])
			first = False
		elif typeDict[member["type"]]["type_of_type"] == "array":
			writeString += arrayCreateReturn(member["type"], funcName, typeDict, struct + "." + member["name"], first)
		elif typeDict[member["type"]]["type_of_type"] == "struct":
			writeString += structCreateReturn(member["type"], funcName, typeDict, struct + "." + member["name"], first)
	return writeString

def writeStub(typeDict, functionList):

	writeString = ""
	### Create declaration for function stub
	for func in functionList:
		writeString += createStubFunction(func)

	with open(fileStub, "a") as file:
		file.write(writeString)
		file.write(writeSupportFuncs(functionList))

def createStubFunction(func):
	writeString = "void __%s(" % func[1]
	writeString += ") {\n"

	### Create read buffer
	if len(func[2]) > 0:
		writeString += "\tchar readBuffer[512];\n\n"

	writeString += stubCreateArgDecls(func[2], typeDict)
	writeString += createReturnDecl(func[0])
	
	### Declare length variable for parsing readBuffer
	if len(func[2]) > 0:
		writeString += "\tint readLen = 0;\n"

	writeString += "\n"
	writeString += "\t//\n\t// Time to actually call the function\n\t//\n"
	writeString += "\tc150debug->printf(C150RPCDEBUG,\"%s: invoking %s()\");\n" % (fileProxy, func[1])
	writeString += "\tusleep(250000);\n"

	if len(func[2]) > 0:
		writeString += "\tRPCSTUBSOCKET->read(readBuffer, sizeof(readBuffer));\n\n"

	writeString += readArgsFromNetwork(func[2])
	writeString += createFunctionCall(func)
	writeString += createReturnStatement(func[0], "ret", typeDict)

	writeString += "\tc150debug->printf(C150RPCDEBUG,\"%s: returned from %s() -- responding to client\");\n" % (fileStub, func[1])
	writeString += "}\n\n"

	return writeString

def stubCreateArgDecls(args, typeDict):
	writeString = ""
	for arg in args:
		writeString += stubCreateArgDecl(arg, typeDict)
	return writeString

def stubCreateArgDecl(arg, typeDict):
	writeString = ""
	typeOfType = typeDict[arg["type"]]["type_of_type"]
	if typeOfType == "builtin":
		writeString += "\t%s %s;\n" % (arg["type"], arg["name"])
	elif typeOfType == "array":
		memberType = typeDict[arg["type"]]["member_type"]
		bracketString = "[%s]" % typeDict[arg["type"]]["element_count"]
		while typeDict[memberType]["type_of_type"] == "array":
			bracketString += "[%s]" % typeDict[memberType]["element_count"]
			memberType = typeDict[memberType]["member_type"]
		baseType = memberType
		writeString += "\t%s %s%s;\n" % (baseType, arg["name"], bracketString)
	elif typeOfType == "struct":
		writeString += "\tstruct %s %s;\n" % (arg["type"], arg["name"])
	return writeString

def createReturnDecl(returnType):
	writeString = ""
	if returnType != "void":
		if typeDict[returnType]["type_of_type"] == "struct":
			writeString += "\tstruct %s ret;\n" % returnType
		else:
			writeString += "\t%s ret;\n" % returnType
	return writeString

def readArgsFromNetwork(args):
	writeString = "\t//\n\t// Read args from readBuffer\n\t//\n"
	first = True;
	for arg in args:
		typeString = arg["type"]
		name = arg["name"]
		if typeString == "int":
			# ret is tuple (string, bool)
			ret = readInt(name, first, 1)
			writeString += ret[0]
			first = ret[1]
		elif typeString == "float":
			ret = readFloat(name, first, 1)
			writeString += ret[0]
			first = ret[1]
		elif typeString == "string":
			ret = readString(name, first, 1)
			writeString += ret[0]
			first = ret[1]
		elif typeDict[typeString]["type_of_type"] == "array":
			ret = readArray(first, arg["type"], arg["name"], typeDict)
			writeString += ret[0]
			first = ret[1]
		elif typeDict[typeString]["type_of_type"] == "struct":
			ret = readStruct(first, arg["type"], arg["name"], typeDict)
			writeString += ret[0]
			first = ret[1]

	writeString += "\n"

	return writeString

def createReturnStatement(retType, retName, typeDict):
	writeString = ""
	if retType == "void":
		writeString += createVoidReturn()
	elif retType == "int":
		writeString += createIntReturn(retName, retName)
	elif retType == "float":
		writeString += createFloatReturn(retName, retName)
	elif retType == "string":
		writeString += createStringReturn(retName, retName)
	elif typeDict[retType]["type_of_type"] == "struct":
		writeString += createStructReturn(retType, retName, typeDict)
	else:
		print("Error: Bad return type")

	return writeString

def createVoidReturn():
	writeString = "\tstring done = \"DONE\";\n"
	writeString += "\tRPCSTUBSOCKET->write(done, done.length()+1);\n"
	return writeString

def createIntReturn(retName, varName):
	retName = retName.replace('[','').replace(']', '').replace('.','')
	writeString = "\tstring %sStr = to_string(%s);\n" % (retName, varName)
	writeString += "\tRPCSTUBSOCKET->write(%sStr.c_str(), %sStr.length()+1);\n\n" % (retName, retName)
	return writeString

def createFloatReturn(retName, varName):
	retName = retName.replace('[','').replace(']', '').replace('.','')
	writeString = "\tstring %sStr = to_string(%s);\n" % (retName, varName)
	writeString += "\tRPCSTUBSOCKET->write(%sStr.c_str(), %sStr.length()+1);\n\n" % (retName, retName)
	return writeString

def createStringReturn(retName, varName):
	retName = retName.replace('[','').replace(']', '').replace('.','')
	writeString = "\tstring %sStr = %s;\n" % (retName, varName)
	writeString += "\tRPCSTUBSOCKET->write(%sStr.c_str(), %sStr.length()+1);\n\n" % (retName, retName)
	return writeString

def createStructReturn(retType, retName, typeDict):
	# To do: change fullName variable name
	writeString = ""
	print retName
	members = typeDict[retType]["members"]
	for m in members:
		mName = m["name"]
		mType = m["type"]
		strName = "%s%s" % (retName, mName)
		fullName = "%s.%s" % (retName, mName)
		if mType == "int":
			writeString += createIntReturn(fullName, fullName)
		elif mType == "float":
			writeString += createFloatReturn(fullName, fullName)
		elif mType == "string":
			writeString += createStringReturn(fullName, fullName)
		elif typeDict[mType]["type_of_type"] == "array":
			writeString += createArrayReturn(mType, fullName, typeDict)
		elif typeDict[mType]["type_of_type"] == "struct":
			writeString += createStructReturn(mType, fullName, typeDict)
		else:
			print "Error"
	return writeString

def createArrayReturn(retType, retName, typeDict):
	writeString = ""
	memberType = typeDict[retType]["member_type"]
	elemCount  = typeDict[retType]["element_count"]

	depth = 1
	while typeDict[memberType]["type_of_type"] == "array":
		depth += 1
		memberType = typeDict[memberType]["member_type"]
	writeString += arrayNDToArgType(depth, retType, retName, typeDict)

	bracketString = "%s[i]" % retName
	for i in range(depth - 1):
		bracketString += "[%s]" % chr(ord('i') + (i + 1))
	
	if memberType == "int":
		writeString += createIntReturn(bracketString, bracketString)
	elif memberType == "float":
		writeString += createFloatReturn(bracketString, bracketString)
	elif memberType == "string":
		writeString += createStringReturn(bracketString, bracketString)
	elif typeDict[memberType]["type_of_type"] == "struct":
		writeString += createStructReturn(memberType, bracketString, typeDict)

	for i in range(depth, 0, -1):
		writeString += "\t" * i + "}\n"
	writeString += "\n"
	return writeString

def arrayNDToArgType(depth, argType, argName, typeDict):
	writeString = ""
	iterVar = 'i'
	for i in range(depth):
		elementCount = typeDict[argType]["element_count"]
		writeString += '\t' * (i + 1)
		writeString += "for (int %s=0; %s<%s; %s++) {\n" % (iterVar, iterVar, elementCount, iterVar)
		iterVar = chr(ord(iterVar) + 1)
		argType = typeDict[argType]["member_type"]
	return writeString

def createFunctionCall(func):
	writeString = ""
	firstArg = True
	if func[0] == "void":
		writeString += "\t%s(" % (func[1])
	else:
		writeString += "\tret = %s(" % (func[1])
	for arg in func[2]:
		if firstArg:
			writeString += "%s" % (arg["name"])
			firstArg = False
		else:
			writeString += ", %s" % (arg["name"])
	writeString += ");\n"

	return writeString

def readInt(argName, first, tabs):
	writeString = "\t" * tabs + "%s = stoi(string(&(readBuffer[readLen])));\n" % (argName)
	writeString += "\t" * tabs + "readLen += to_string(%s).length()+1;\n" % (argName)
	return (writeString, False)

def readFloat(argName, first, tabs):
	writeString = "\t" * tabs + "%s = stof(string(&(readBuffer[readLen])));\n" % (argName)
	writeString += "\t" * tabs + "readLen += to_string(%s).length()+1;\n" % (argName)
	return (writeString, False)

def readString(argName, first, tabs):
	writeString = "\t" * tabs + "%s = &(readBuffer[readLen]);\n" % (argName)
	writeString += "\t" * tabs + "readLen += %s.length()+1;\n" % (argName)
	return (writeString, False)

def readStruct(first, argType, argName, typeDict):
	members = typeDict[argType]["members"]
	writeString = ""
	first = False
	for m in members:
		mType = m["type"]
		mName = m["name"]
		fullName = "%s.%s" % (argName, mName)
		if mType == "int":
			writeString += readInt(fullName, first, 2)[0]
		elif mType == "float":
			writeString += readFloat(fullName, first, 2)[0]
		elif mType == "string":
			writeString += readString(fullName, first, 2)[0]
		else:
			typeOfType = typeDict[mType]["type_of_type"]
			if typeOfType == "array":
				writeString += readArray(first, mType, fullName, typeDict)[0]
			elif typeOfType == "struct":
				writeString += readStruct(first, mType, fullName, typeDict)[0]	

	return (writeString, False)

def readArray(first, argType, argName, typeDict):
	writeString = ""
	typeObj = typeDict[argType]
	memberType = typeObj["member_type"]

	depth = 1
	while typeDict[memberType]["type_of_type"] == "array":
		depth += 1
		memberType = typeDict[memberType]["member_type"]
	writeString += arrayNDToArgType(depth, argType, argName, typeDict)

	bracketString = "%s[i]" % argName
	for i in range(depth - 1):
		bracketString += "[%s]" % chr(ord('i') + (i + 1))
	print "DEPTH: " + str(depth)
	if memberType == "int":
		writeString += readInt(bracketString, first, depth + 2)[0]
	elif memberType == "float":
		writeString += readFloat(bracketString, first, depth + 2)[0]
	elif memberType == "string":
		writeString += readString(bracketString, first, depth + 2)[0]
	elif typeDict[memberType]["type_of_type"] == "struct":
		writeString += readStruct(first, memberType, bracketString, typeDict)[0]

	for i in range(depth, 0, -1):
		writeString += "\t" * i + "}\n"

	return (writeString, False)

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

def readNDArray(depth, argType, argName, typeDict):
	writeString = ""
	iterVar = 'i'
	for i in range(depth):
		elementCount = typeDict[argType]["element_count"]
		writeString += '\t' * (i + 1)
		writeString += "for (int %s=0; %s<%s; %s++) {\n" % (iterVar, iterVar, elementCount, iterVar)
		iterVar = chr(ord(iterVar) + 1)
		argType = typeDict[argType]["member_type"]
	return writeString

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
