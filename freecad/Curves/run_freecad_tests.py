#!/usr/bin/env python3

import subprocess
import sys
import os

def run_tests_with_freecad_appimage():
    """Run tests using FreeCAD AppImage"""
    
    # Find FreeCAD AppImage
    appimage_candidates = [
        "FreeCAD_0.21.2-Linux-x86_64.AppImage",
        "FreeCAD-latest-Linux-x86_64.AppImage",
        "FreeCAD.AppImage"
    ]
    
    freecad_appimage = None
    for candidate in appimage_candidates:
        if os.path.exists(candidate):
            freecad_appimage = candidate
            break
    
    if not freecad_appimage:
        print("❌ FreeCAD AppImage not found!")
        print("Please download it and place in current directory:")
        print("wget https://github.com/FreeCAD/FreeCAD/releases/download/0.21.2/FreeCAD_0.21.2-Linux-x86_64.AppImage")
        return False
    
    print(f"✅ Found FreeCAD AppImage: {freecad_appimage}")
    
    # Make sure it's executable
    os.chmod(freecad_appimage, 0o755)
    
    # Run the test
    cmd = [
        f"./{freecad_appimage}",
        "--console",  # Run in console mode
        "-P", "test_mixed_curve_freecad.py"  # Execute Python script
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Test execution timed out!")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_tests_with_freecad_appimage()
    sys.exit(0 if success else 1)