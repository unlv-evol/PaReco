#!/bin/bash

case "$OSTYPE" in
  solaris*) 
    echo "SOLARIS: This version of Operating System is not yet supported. Please try again later!"
    ;;
  darwin*)
    echo "You are using MacOS X"
    echo `brew install libmagic`
    ;; 
  linux*)
    echo `apt-get install libmagic-dev`
    ;;
  bsd*)
    echo "BSD: This version of Operating System is not yet supported. Please try again later!"
    ;;
  msys*)
    echo "WINDOWS: This version of Operating System is not yet supported. Please try again later!"
    ;;
  cygwin*)
    echo "ALSO WINDOWS: This version of Operating System is not yet supported. Please try again later!"
    ;;
  *)
    echo "unknown: $OSTYPE - This version of Operating System is not yet supported. Please try again later!"
    ;;
esac