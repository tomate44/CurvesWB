#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import shutil
import sys
import os
import unittest
from pathlib import Path

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


def pip_install(pkg_name):
    if 'PYTHONHOME' in os.environ:
        del os.environ['PYTHONHOME']

    import subprocess
    from pathlib import Path as pyPath

    import addonmanager_utilities as utils

    pip_exe = pyPath(utils.get_python_exe()).with_stem('pip')
    vendor_path = pyPath(utils.get_pip_target_directory()).resolve()
    if not vendor_path.is_dir():
        vendor_path.mkdir(parents=True)

    p = subprocess.Popen(
        [pip_exe, 'install', '--disable-pip-version-check', '--target', vendor_path, pkg_name],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    for line in iter(p.stdout.readline, b''):
        if line:
            print(line.decode('utf-8'), end='')
    print()

    for err in iter(p.stderr.readline, b''):
        if err:
            print(err.decode('utf-8'), end='')
    print()

    p.stdout.close()
    p.stderr.close()
    p.wait()


try:
    import coverage

    print("✅ Coverage module available")
except ImportError:
    print("❌ Coverage module not available - installing...")

    try:
        pip_install('coverage')
        import coverage

        print("✅ Coverage installed and imported")
    except Exception as e:
        print(f"❌ Failed to install coverage: {e}")

coverage_dir = Path("coverage_reports")
shutil.rmtree(coverage_dir, ignore_errors=True)

from tests.test_mixed_curve_freecad import TestMixedCurveWithFreeCAD
