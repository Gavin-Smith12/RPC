#include "arithmetic.idl"

#include "rpcproxyhelper.h"

#include <cstdio>
#include <cstring>
#include "c150debug.h"

using namespace C150NETWORK;  // for all the comp150 utilities 

int add(int x, int y) {
    char readBuffer[512];

    c150debug->printf(C150RPCDEBUG,"simplefunction.proxy.cpp: add() invoked");
    RPCPROXYSOCKET->write("func1", strlen("func1")+1);
    RPCPROXYSOCKET->write(to_string(x), strlen(to_string(x))+1);
    RPCPROXYSOCKET->write(to_string(y), strlen(to_string(y))+1);

    c150debug->printf(C150RPCDEBUG,"simplefunction.proxy.cpp: add() invocation sent, waiting for response");
    RPCPROXYSOCKET->read(readBuffer, sizeof(readBuffer)); // only legal response is DONE

    try {
        int value = stoi(readBuffer);
    } catch {
        throw C150Exception("simplefunction.proxy: add() received invalid response from the server");
    }

    c150debug->printf(C150RPCDEBUG,"simplefunction.proxy.cpp: func1() successful return from remote call");

    return value;
}

int subtract(int x, int y) {
    char readBuffer[512];

    c150debug->printf(C150RPCDEBUG,"simplefunction.proxy.cpp: add() invoked");
    RPCPROXYSOCKET->write("func1", strlen("func1")+1);
    RPCPROXYSOCKET->write(to_string(x), strlen(to_string(x))+1);
    RPCPROXYSOCKET->write(to_string(y), strlen(to_string(y))+1);

    c150debug->printf(C150RPCDEBUG,"simplefunction.proxy.cpp: add() invocation sent, waiting for response");
    RPCPROXYSOCKET->read(readBuffer, sizeof(readBuffer)); // only legal response is DONE

    try {
        int value = stoi(readBuffer);
    } catch {
        throw C150Exception("simplefunction.proxy: add() received invalid response from the server");
    }

    c150debug->printf(C150RPCDEBUG,"simplefunction.proxy.cpp: func1() successful return from remote call");

    return value;
}

int multiply(int x, int y) {
    char readBuffer[512];

    c150debug->printf(C150RPCDEBUG,"simplefunction.proxy.cpp: add() invoked");
    RPCPROXYSOCKET->write("func1", strlen("func1")+1);
    RPCPROXYSOCKET->write(to_string(x), strlen(to_string(x))+1);
    RPCPROXYSOCKET->write(to_string(y), strlen(to_string(y))+1);

    c150debug->printf(C150RPCDEBUG,"simplefunction.proxy.cpp: add() invocation sent, waiting for response");
    RPCPROXYSOCKET->read(readBuffer, sizeof(readBuffer)); // only legal response is DONE

    try {
        int value = stoi(readBuffer);
    } catch {
        throw C150Exception("simplefunction.proxy: add() received invalid response from the server");
    }

    c150debug->printf(C150RPCDEBUG,"simplefunction.proxy.cpp: func1() successful return from remote call");

    return value;
}

int divide(int x, int y) {
    char readBuffer[512];

    c150debug->printf(C150RPCDEBUG,"simplefunction.proxy.cpp: add() invoked");
    RPCPROXYSOCKET->write("func1", strlen("func1")+1);
    RPCPROXYSOCKET->write(to_string(x), strlen(to_string(x))+1);
    RPCPROXYSOCKET->write(to_string(y), strlen(to_string(y))+1);

    c150debug->printf(C150RPCDEBUG,"simplefunction.proxy.cpp: add() invocation sent, waiting for response");
    RPCPROXYSOCKET->read(readBuffer, sizeof(readBuffer)); // only legal response is DONE

    try {
        int value = stoi(readBuffer);
    } catch {
        throw C150Exception("simplefunction.proxy: add() received invalid response from the server");
    }

    c150debug->printf(C150RPCDEBUG,"simplefunction.proxy.cpp: func1() successful return from remote call");

    return value;
}