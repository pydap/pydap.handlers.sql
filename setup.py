from setuptools import setup, find_packages
import sys, os


version = '0.4.0'

install_requires = [
    # List your project dependencies here.
    # For more details, see:
    # http://packages.python.org/distribute/setuptools.html#declaring-dependencies
    'SQLAlchemy',
    'Pydap>=3.2',
    'PyYAML',
    'Numpy',
]


setup(name='pydap.handlers.sql',
    version=version,
    description="An SQL handler for Pydap",
    long_description="",
    classifiers=[
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
    keywords="sql database opendap dods dap data science climate oceanography meteorology'",
    author='Roberto De Almeida',
    author_email='roberto@dealmeida.net',
    url='http://pydap.org/handlers.html#sql',
    license='MIT',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    namespace_packages = ['pydap', 'pydap.handlers'],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    entry_points="""
        [pydap.handler]
        sql = pydap.handlers.sql:SQLHandler
    """,
)
