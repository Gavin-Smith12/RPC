// --------------------------------------------------------------
//
//                        arrayandstructclient.cpp
//
//        Authors: Gavin Smith and Ravi Serota       
//   
//
//        This is a test function to test the rpcgenerate's ability to 
//        deal with struct and structs within structs, as well as arrays 
//        within structs.		      
//
//        COMMAND LINE
//
//              arrayandstruct <servername> 
//     
// --------------------------------------------------------------

#include "rpcproxyhelper.h"

#include "c150debug.h"
#include "c150grading.h"
#include <fstream>
#include <string>

using namespace std;          // for C++ std library
using namespace C150NETWORK;  // for all the comp150 utilities 

#include "arrayandstruct.idl"

// forward declarations
void setUpDebugLogging(const char *logname, int argc, char *argv[]);


// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
//
//                    Command line arguments
//
// The following are used as subscripts to argv, the command line arguments
// If we want to change the command line syntax, doing this
// symbolically makes it a bit easier.
//
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

const int serverArg = 1;     // server name is 1st arg


// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
//
//                           main program
//
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

int 
main(int argc, char *argv[]) {

     //
     //  Set up debug message logging
     //
     setUpDebugLogging("simplefunctionclientdebug.txt",argc, argv);

     //
     // Make sure command line looks right
     //
     if (argc != 2) {
       fprintf(stderr,"Correct syntxt is: %s <servername> \n", argv[0]);
       exit(1);
     }

     //
     //  DO THIS FIRST OR YOUR ASSIGNMENT WON'T BE GRADED!
     //
     
     GRADEME(argc, argv);

     //
     //     Call the functions and see if they return
     //
     try {
       int result; 
       string strResult;
       test1 structResult;
       int argArray[100];
       test2 structArg;

       //
       // Set up the socket so the proxies can find it
       //
       rpcproxyinitialize(argv[serverArg]);

       // Function takes in the 3 members of the test1 struct and returns 
       // that type of struct
       *GRADING << "Calling returnStruct(5, 7.5, \"hello\")" << endl;
       structResult = returnStruct(5, 7.5, "hello");            
       *GRADING << "Returned from returnStruct(5, 7.5, \"hello\")." << endl;
       *GRADING << "Result: test1.a= " << structResult.a << ", test1.b= " << structResult.b << " test1.c= " << structResult.c << endl;
       
       for(int i = 0; i < 100; i++) {
          argArray[i] = 5;
       }
      
       // Function takes in an array with 100 members and returns the sum
       *GRADING << "Calling sumLargeArray(int[100])" << endl;
       result = sumLargeArray(argArray);                          
       *GRADING << "Returned from sumLargeArray(int[100]). Result= " << result << endl;

       structArg.d[0][0] = 5;
       structArg.structarr[0].c = "returned!";
       structArg.structarr[1].a = 6;
       structArg.structarr[1].b = 14.4;
       structArg.structarr[1].c = "done!!!";

       // Function takes in a test2 struct and returns the string member of the
       // test1 struct contained within the test2 struct
       *GRADING << "Calling getStructMember(test2 x), expecting result \"returned!\"" << endl;
       strResult = getStructMember(structArg);                         
       *GRADING << "Returned from getStructMember(test2 x). Result= " << result << endl;

       // Function takes in a test2 struct and returns the whole test1 struct member
       *GRADING << "Calling returnMemberStruct(test2 x), expecting result \"done!!!\"" << endl;
       structResult = returnMemberStruct(structArg);                         
       *GRADING << "Result: test1.a= " << structResult.a << ", test1.b= " << structResult.b << " test1.c= " << structResult.c << endl;


     }

     //
     //  Handle networking errors -- for now, just print message and give up!
     //
     catch (C150Exception& e) {
       // Write to debug log
       c150debug->printf(C150ALWAYSLOG,"Caught C150Exception: %s\n",
			 e.formattedExplanation().c_str());
       // In case we're logging to a file, write to the console too
       cerr << argv[0] << ": caught C150NetworkException: " << e.formattedExplanation() << endl;
     }

     return 0;
}

void setUpDebugLogging(const char *logname, int argc, char *argv[]) {

     
     ofstream *outstreamp = new ofstream(logname);
     DebugStream *filestreamp = new DebugStream(outstreamp);
     DebugStream::setDefaultLogger(filestreamp);

     c150debug->setPrefix(argv[0]);
     c150debug->enableTimestamp(); 

     c150debug->enableLogging(C150ALLDEBUG | C150RPCDEBUG | C150APPLICATION | C150NETWORKTRAFFIC | 
			      C150NETWORKDELIVERY); 
}
