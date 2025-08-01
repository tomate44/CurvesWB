import os
import sys
from pathlib import Path

import coverage

PACKAGES = ['freecad.Curves']

class CoverageReportCollector:
    """Collect coverage report from FreeCAD environment"""

    @classmethod
    def create_collector(cls):
        cov = coverage.Coverage(
            source_pkgs=['freecad.Curves'],
            omit=['*/test_*', '*/tests/*', '*/__pycache__/*'],
            include=['*.py'],
            branch=True,
        )

        # Add current directory to Python path
        current_dir = os.getcwd()
        sys.path.insert(0, current_dir)
        return cov

    @classmethod
    def collect(cls):
        """Collect coverage report from FreeCAD environment"""

        # Generate coverage reports
        coverage_dir = Path("coverage_reports")
        coverage_dir.mkdir(exist_ok=True)

        cov = cls.create_collector()
        print(f"coverage dir: {coverage_dir.absolute()}")
        # Text report
        with open(coverage_dir / "coverage.txt", "w") as f:
            cov.report(file=f, show_missing=True, ignore_errors=True)

        # HTML report
        cov.html_report(directory=str(coverage_dir / "html"))

        # XML report (for CI/CD)
        cov.xml_report(outfile=str(coverage_dir / "coverage.xml"))

        print(f"✅ Coverage reports generated in {{coverage_dir}}")

        # Print summary
        total_coverage = cov.report(show_missing=False)
        print(f"Total Coverage: {total_coverage:.1f}%")

CoverageReportCollector.create_collector()