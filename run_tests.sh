#!/usr/bin/env bash
set -e

if [ ! -f ./FreeCAD.AppImage ]; then
    wget https://github.com/FreeCAD/FreeCAD/releases/download/weekly-2025.07.29/FreeCAD_weekly-2025.07.29-Linux-x86_64-py311.AppImage -O FreeCAD.AppImage
    chmod +x ./FreeCAD.AppImage
fi

./FreeCAD.AppImage -M `pwd` -t freecad.Curves.TestCurves