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

#include "arithmetic.idl"

struct test3 {
    string yay;
};

struct test2 {
    test3 woo[2][2];
};

struct test1 {
    test2 t2;
    test3 t3[2]
};

test1 add(test1 a) {
    cout << "the string is " << a.t2.woo[0][0].yay << endl;
    a.t2.woo[0][0].yay = "goodbye";
    cout << "the string is now" << a.t2.woo[0][0].yay << endl;
    return test1;
}   

int subtract(int x, int y) {
  return x-y;
}

int multiply(int x, int y) {
  return x*y;
}

int divide(int x, int y) {
  return x/y;
}

