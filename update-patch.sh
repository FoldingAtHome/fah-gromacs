#!/bin/bash

PACKAGE=gromacs-4.5.4
ARCHIVE=$PACKAGE.tar.gz

if [ ! -e $PACKAGE.orig ]; then
  if [ ! -e $ARCHIVE ]; then
    echo "Need $ARCHIVE"
    exit 1
  fi

  (mkdir orig &&
  cd orig &&
  tar xzf ../$ARCHIVE &&
  cd .. &&
  mv orig/* $PACKAGE.orig &&
  rmdir orig) || (
    echo "Failed to unpack $ARCHIVE"
    exit 1
  )
fi

diff -aur $PACKAGE.orig $PACKAGE 2>/dev/null |
  sed 's/^\(\(\+\+\+\)\|\(---\)\) \([^\/]*\)\.orig/\1 \4/' |
  grep -v '^Only in' >$PACKAGE-fah.patch
