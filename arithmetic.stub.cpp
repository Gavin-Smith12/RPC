#include "arithmetic.idl"

#include "rpcstubhelper.h"

#include <cstdio>
#include <cstring>
#include "c150debug.h"

using namespace C150NETWORK;  // for all the comp150 utilities 

void __add() {
  char varBuffer[512];
  // char doneBuffer[512];
  int x, y, res;

  //
  // Time to actually call the function 
  //
  c150debug->printf(C150RPCDEBUG,"arithmetic.stub.cpp: invoking add()");
  RPCSTUBSOCKET->read(varBuffer, sizeof(varBuffer));
  x = stoi((string) varBuffer);
  size_t xLen = to_string(x).length();
  cout << x << endl;
  // RPCSTUBSOCKET->read(varBuffer, sizeof(varBuffer));
  y = stoi(string(&(varBuffer[xLen+1])));
  cout << y << endl;
  res = add(x, y);
  string resStr = to_string(res);

  //
  // Send the response to the client
  //
  // If func1 returned something other than void, this is
  // where we'd send the return value back.
  //
  c150debug->printf(C150RPCDEBUG,"arithmetic.stub.cpp: returned from  add() -- responding to client");
  RPCSTUBSOCKET->write(resStr.c_str(), resStr.length()+1);
}

void __subtract() {
  char varBuffer[512];

  int x, y, res;
  //
  // Time to actually call the function 
  //
  c150debug->printf(C150RPCDEBUG,"arithmetic.stub.cpp: invoking subtract()");
  RPCSTUBSOCKET->read(varBuffer, sizeof(varBuffer));
  x = stoi((string) varBuffer);
  size_t xLen = to_string(x).length();
  cout << x << endl;
  y = stoi(string(&(varBuffer[xLen+1])));
  cout << y << endl;
  res = subtract(x, y);
  string resStr = to_string(res);
  //
  // Send the response to the client
  //
  // If func1 returned something other than void, this is
  // where we'd send the return value back.
  //
  c150debug->printf(C150RPCDEBUG,"arithmetic.stub.cpp: returned from  subtract() -- responding to client");
  RPCSTUBSOCKET->write(resStr.c_str(), resStr.length()+1);
}

void __multiply() {
  char varBuffer[512];

  int x, y, res;

  //
  // Time to actually call the function 
  //
  c150debug->printf(C150RPCDEBUG,"arithmetic.stub.cpp: invoking multiply()");
  RPCSTUBSOCKET->read(varBuffer, sizeof(varBuffer));
  x = stoi((string) varBuffer);
  size_t xLen = to_string(x).length();
  cout << x << endl;
  y = stoi(string(&(varBuffer[xLen+1])));
  cout << y << endl;
  res = multiply(x, y);
  string resStr = to_string(res);

  //
  // Send the response to the client
  //
  // If func1 returned something other than void, this is
  // where we'd send the return value back.
  //
  c150debug->printf(C150RPCDEBUG,"arithmetic.stub.cpp: returned from multiply() -- responding to client");
  RPCSTUBSOCKET->write(resStr.c_str(), resStr.length()+1);
}

void __divide() {
  char varBuffer[512];

  int x, y, res;

  //
  // Time to actually call the function 
  //
  c150debug->printf(C150RPCDEBUG,"arithmetic.stub.cpp: invoking divide()");
  RPCSTUBSOCKET->read(varBuffer, sizeof(varBuffer));
  x = stoi((string) varBuffer);
  size_t xLen = to_string(x).length();
  cout << x << endl;
  y = stoi(string(&(varBuffer[xLen+1])));
  cout << y << endl;
  res = divide(x, y);
  string resStr = to_string(res);
 

  //
  // Send the response to the client
  //
  // If func1 returned something other than void, this is
  // where we'd send the return value back.
  //
  c150debug->printf(C150RPCDEBUG,"arithmetic.stub.cpp: returned from  divide() -- responding to client");
  RPCSTUBSOCKET->write(resStr.c_str(), resStr.length()+1);
}

void getFunctionNamefromStream();

void __badFunction(char *functionName) {
  char doneBuffer[5] = "BAD";  // to write magic value DONE + null


  //
  // Send the response to the client indicating bad function
  //

  c150debug->printf(C150RPCDEBUG,"simplefunction.stub.cpp: received call for nonexistent function %s()",functionName);
  RPCSTUBSOCKET->write(doneBuffer, strlen(doneBuffer)+1);
}



// ======================================================================
//
//                        COMMON SUPPORT FUNCTIONS
//
// ======================================================================

// forward declaration
void getFunctionNameFromStream(char *buffer, unsigned int bufSize);



//
//                         dispatchFunction()
//
//   Called when we're ready to read a new invocation request from the stream
//

void dispatchFunction() {


  char functionNameBuffer[50];

  //
  // Read the function name from the stream -- note
  // REPLACE THIS WITH YOUR OWN LOGIC DEPENDING ON THE 
  // WIRE FORMAT YOU USE
  //
  getFunctionNameFromStream(functionNameBuffer,sizeof(functionNameBuffer));

  //
  // We've read the function name, call the stub for the right one
  // The stub will invoke the function and send response.
  //

  if (!RPCSTUBSOCKET-> eof()) {
    if (strcmp(functionNameBuffer,"add") == 0)
      __add();
    else   if (strcmp(functionNameBuffer,"subtract") == 0)
      __subtract();
    else   if (strcmp(functionNameBuffer,"multiply") == 0)
      __multiply();
    else   if (strcmp(functionNameBuffer,"divide") == 0)
      __divide();
    else
      __badFunction(functionNameBuffer);
  }
}

 
//
//                   getFunctionNamefromStream
//
//   Helper routine to read function name from the stream. 
//   Note that this code is the same for all stubs, so can be generated
//   as boilerplate.
//
//   Important: this routine must leave the sock open but at EOF
//   when eof is read from client.
//
void getFunctionNameFromStream(char *buffer, unsigned int bufSize) {
  unsigned int i;
  char *bufp;    // next char to read
  bool readnull;
  ssize_t readlen;             // amount of data read from socket
  
  //
  // Read a message from the stream
  // -1 in size below is to leave room for null
  //
  readnull = false;
  bufp = buffer;
  for (i=0; i< bufSize; i++) {
    readlen = RPCSTUBSOCKET-> read(bufp, 1);  // read a byte
    // check for eof or error
    if (readlen == 0) {
      break;
    }
    // check for null and bump buffer pointer
    if (*bufp++ == '\0') {
      readnull = true;
      break;
    }
  }
  
  //
  // With TCP streams, we should never get a 0 length read
  // except with timeouts (which we're not setting in pingstreamserver)
  // or EOF
  //
  if (readlen == 0) {
    c150debug->printf(C150RPCDEBUG,"simplefunction.stub: read zero length message, checking EOF");
    if (RPCSTUBSOCKET-> eof()) {
      c150debug->printf(C150RPCDEBUG,"simplefunction.stub: EOF signaled on input");

    } else {
      throw C150Exception("simplefunction.stub: unexpected zero length read without eof");
    }
  }

  //
  // If we didn't get a null, input message was poorly formatted
  //
  else if(!readnull) 
    throw C150Exception("simplefunction.stub: method name not null terminated or too long");

  
  //
  // Note that eof may be set here for our caller to check
  //

}