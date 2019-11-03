#include "arithmetic.idl"

#include "rpcproxyhelper.h"

#include <cstdio>
#include <cstring>
#include "c150debug.h"

using namespace C150NETWORK;  // for all the comp150 utilities 

int add(int x, int y) {
    char readBuffer[512];

	string xStr, yStr;
	xStr = to_string(x);
	yStr = to_string(y);

    c150debug->printf(C150RPCDEBUG,"arithmetic.proxy.cpp: add() invoked");
    RPCPROXYSOCKET->write("add", strlen("add")+1);
    RPCPROXYSOCKET->write(xStr.c_str(), xStr.length()+1);
    RPCPROXYSOCKET->write(yStr.c_str(), yStr.length()+1);

    c150debug->printf(C150RPCDEBUG,"arithmetic.proxy.cpp: add() invocation sent, waiting for response");
    RPCPROXYSOCKET->read(readBuffer, sizeof(readBuffer));

	int value;
    try {
        value = stoi(readBuffer);
    } catch (invalid_argument& e) {
        throw C150Exception("arithmetic.proxy: add() received invalid response from the server");
    }

    c150debug->printf(C150RPCDEBUG,"arithmetic.proxy.cpp: add() successful return from remote call");

    return value;
}

int subtract(int x, int y) {
    char readBuffer[512];
	string xStr, yStr;
	xStr = to_string(x);
	yStr = to_string(y);

    c150debug->printf(C150RPCDEBUG,"arithmetic.proxy.cpp: add() invoked");
    RPCPROXYSOCKET->write("subtract", strlen("subtract")+1);
    RPCPROXYSOCKET->write(xStr.c_str(), xStr.length()+1);
    RPCPROXYSOCKET->write(yStr.c_str(), yStr.length()+1);

    c150debug->printf(C150RPCDEBUG,"arithmetic.proxy.cpp: subtract() invocation sent, waiting for response");
    RPCPROXYSOCKET->read(readBuffer, sizeof(readBuffer)); // only legal response is DONE

	int value;
    try {
        value = stoi(readBuffer);
    } catch (invalid_argument& e) {
        throw C150Exception("arithmetic.proxy: subtract() received invalid response from the server");
    }

    c150debug->printf(C150RPCDEBUG,"arithmetic.proxy.cpp: subtract() successful return from remote call");

    return value;
}

int multiply(int x, int y) {
    char readBuffer[512];

	string xStr, yStr;
	xStr = to_string(x);
	yStr = to_string(y);

    c150debug->printf(C150RPCDEBUG,"arithmetic.proxy.cpp: add() invoked");
    RPCPROXYSOCKET->write("multiply", strlen("multiply")+1);
    RPCPROXYSOCKET->write(xStr.c_str(), xStr.length()+1);
    RPCPROXYSOCKET->write(yStr.c_str(), yStr.length()+1);

    c150debug->printf(C150RPCDEBUG,"arithmetic.proxy.cpp: multiply() invocation sent, waiting for response");
    RPCPROXYSOCKET->read(readBuffer, sizeof(readBuffer)); // only legal response is DONE
	
	int value;
    try {
        value = stoi(readBuffer);
     } catch (invalid_argument& e) {
        throw C150Exception("arithmetic.proxy: multiply() received invalid response from the server");
    }

    c150debug->printf(C150RPCDEBUG,"arithmetic.proxy.cpp: multiply() successful return from remote call");

    return value;
}

int divide(int x, int y) {
    char readBuffer[512];

	string xStr, yStr;
	xStr = to_string(x);
	yStr = to_string(y);

    c150debug->printf(C150RPCDEBUG,"arithmetic.proxy.cpp: add() invoked");
    RPCPROXYSOCKET->write("divide", strlen("divide")+1);
    RPCPROXYSOCKET->write(xStr.c_str(), xStr.length()+1);
    RPCPROXYSOCKET->write(yStr.c_str(), yStr.length()+1);

    c150debug->printf(C150RPCDEBUG,"arithmetic.proxy.cpp: divide() invocation sent, waiting for response");
    RPCPROXYSOCKET->read(readBuffer, sizeof(readBuffer)); // only legal response is DONE
	
	int value;
    try {
        value = stoi(readBuffer);
     } catch (invalid_argument& e) {
        throw C150Exception("arithmetic.proxy: divide() received invalid response from the server");
    }

    c150debug->printf(C150RPCDEBUG,"arithmetic.proxy.cpp: divide() successful return from remote call");

    return value;
}