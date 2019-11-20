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

test1 add(test1 a) {
    cout << "the string is " << a.t2.woo[0][0].yay << endl;
    a.t2.woo[0][0].yay = "goodbye";
    cout << "the string is now " << a.t2.woo[0][0].yay << endl;
    cout << "the other string is " << a.t2.woo[0][1].yay << endl;
    return a;
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

