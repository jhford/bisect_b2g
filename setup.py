from setuptools import setup, find_packages
setup(
    name = "bisect-b2g",
    version = "0",
    packages = find_packages(),
    entry_points = {
        'console_scripts': [
            'bisect = bisect_b2g.driver:main'
        ]
    },
    install_requires = ["isodate"],

    # metadata for upload to PyPI
    author = "John Ford",
    author_email = "john@johnford.info",
    description = "This program is used to bisect multiple repositories",
    license = "MPL2",
    keywords = "b2g gaia bisect",
    url = "http://github.com/mozilla-b2g/b2g_bisect",   # project home page, if any
)
