// --------------------------------------------------------------
//
//                        arithmetic.cpp
//
//        Author: Noah Mendelsohn         
//   
//
//        Trivial implementations of the routines declared
//        in arithmetic.idl. These are for testing: they
//        just print messages.
//
//       Copyright: 2012 Noah Mendelsohn
//     
// --------------------------------------------------------------

// IMPORTANT! WE INCLUDE THE IDL FILE AS IT DEFINES THE INTERFACES
// TO THE FUNCTIONS WE'RE IMPLEMENTING. THIS MAKES SURE THE
// CODE HERE ACTUALLY MATCHES THE REMOTED INTERFACE
#include <string>
#include <iostream>

using namespace std;

#include "arrayandstruct.idl"

test1 returnStruct(int x, float y, string z) {
    struct test1 ret;
    ret.a = x;
    ret.b = y;
    ret.c = z;
    return ret;
}

int sumLargeArray(int x[100]) {
    int ret = 0;
    for(int i = 0; i < 100; i++) {
        ret += x[i];
    }
    return ret;
}

string getStructMember(test2 x) {
    return x.structarr[0].c;
}

test1 returnMemberStruct(test2 x) {
    return x.structarr[1];
}

