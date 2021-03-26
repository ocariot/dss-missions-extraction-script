from setuptools import setup, find_packages

setup(
    name="OCARIoT Missions and DSS Data Exporter",
    version="0.1",
    packages=find_packages(),
    scripts=['config.py', 'ocariot_platform_export.py'],

    install_requires=['requests', 'python-dateutil', 'pandas', 'openpyxl'],

    # metadata to display on PyPI
    author="João Oliveira",
    author_email="jpd.oliveira@unparallel.pt",
    description="OCARIoT Data exporter",
    keywords="OCARIoT Data exporter",
    url="https://ocariot.eu",
)
