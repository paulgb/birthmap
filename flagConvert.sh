#!/bin/bash

FLAG_HEIGHT=10

mkdir -p flags-png

for file in `dir flags-svg/`
do
    fname=`basename $file .svg`
    inkscape -f "flags-svg/$file" --export-png="flags-png/$fname.png" --export-height=$FLAG_HEIGHT
done;

