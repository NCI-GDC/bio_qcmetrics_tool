from setuptools import setup, find_packages

setup(
    name = "bio_qcmetrics_tool",
    author = "Kyle Hernandez",
    author_email = "khernandez@bsd.uchicago.edu",
    version = 0.1,
    description = "tools for parsing and formatting QC metrics",
    url = "https://github.com/NCI-GDC/bio_qcmetrics_tool",
    license = "Apache 2.0",
    packages = find_packages(),
    entry_points= {
        'console_scripts': [
            'bio-qcmetrics-tool = bio_qcmetrics_tool.__main__:main'
        ]
    },
    install_requires = [
        'pandas==0.23.0'
    ]
)

