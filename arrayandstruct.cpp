// --------------------------------------------------------------
//
//                        arrayandstruct.cpp
//
//        Authors: Gavin Smith and Ravi Serota       
//   
//
//        Implementations of functions in arrayandstruct.idl.
//        Purpose it to deal with structs and their members.
//     
// --------------------------------------------------------------

#include <string>
#include <iostream>

using namespace std;

#include "arrayandstruct.idl"

// Takes in the members of the test1 struct and returns the struct itself.
test1 returnStruct(int x, float y, string z) {
    struct test1 ret;
    ret.a = x;
    ret.b = y;
    ret.c = z;
    return ret;
}

// Sums a large array and returns the sum.
int sumLargeArray(int x[100]) {
    int ret = 0;
    for(int i = 0; i < 100; i++) {
        ret += x[i];
    }
    return ret;
}

//Returns the member contained within the struct member of the argument.
string getStructMember(test2 x) {
    return x.structarr[0].c;
}

// Returns the entire struct member from the given argument.
test1 returnMemberStruct(test2 x) {
    return x.structarr[1];
}

