import re
from setuptools import setup, find_packages

__version__, = re.findall("__version__ = '(.*)'",
                          open('mrs_logic/__init__.py').read())

setup(
    name='mrs_logic',
    version=__version__,
    description='transform text to logic',
    url='https://github.ibm.com/IBM-Research-AI/mrs_logic',
    platforms='any',
    python_requires='>=3.8',
    packages=find_packages(exclude=('tests', 'tests.*')),
    package_data={
        'mrs_logic.ukb': ['wn30_dict.txt', 'wn30g.bin'],
        'mrs_logic.utool': ['utool-3.4.jar'],
    },
    install_requires=[
        'jpype1',
        'more-itertools',
        'pydelphin',
        'pydot',
        'setuptools',
        'z3-solver',
    ],
    extras_require={
        'docs': [
            'myst-parser',
            'pydata_sphinx_theme',
        ],
        'tests': [
            'isort',
            'pytest',
            'pytest-cov',
            'tox',
        ],
    },
)
