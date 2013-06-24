from setuptools import setup, find_packages
import sys, os


version = '0.4'

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
    long_description="""
This handler allows Pydap to server data from any relational database supported
by `SQLAlchemy <http://www.sqlalchemy.org/>`_. Each dataset is represented by a
YAML file (with extension ``.sql``) that defines the database connection,
variables and other associated metadata. Here's a simple example:

.. code-block:: yaml

    # These parameters are mandatory; they define the database to connect and 
    # the table holding the data. Note that table might be a selection.
    database:
        dsn: 'sqlite:///simple.db'
        table: test

    # This is just metadata defining the dataset; no attributes are required.
    dataset:
        NC_GLOBAL:
            history: Created by the Pydap SQL handler
            dataType: Station
            Conventions: GrADS

        contact: roberto@dealmeida.net
        name: test_dataset
        owner: Roberto De Almeida
        version: 1.0
        last_modified: !Query 'SELECT time FROM test ORDER BY time DESC LIMIT 1;'

    # This is just metadata defining the sequence; no attributes are required.
    sequence:
        name: simple
        items: !Query 'SELECT COUNT(id) FROM test'

    # Each variable must have an attribute called ``col``, referencing the 
    # column; all other are optional.
    _id:
        col: id
        long_name: sequence id
        missing_value: -9999

    lon:
        col: lon
        axis: X
        grads_dim: x
        long_name: longitude
        units: degrees_east
        missing_value: -9999
        global_range: [-180, 180]
        valid_range: !Query 'SELECT min(lon), max(lon) FROM test'

    lat:                                                                            
        col: lat                                                                    
        axis: Y                                                                     
        grads_dim: y                                                                
        long_name: latitude                                                         
        units: degrees_north                                                        
        missing_value: -9999                                                        
        global_range: [-90, 90]                                                     
        valid_range: !Query 'SELECT min(lat), max(lat) FROM test'                   
                                                                                    
    time:                                                                           
        col: time                                                                   
        axis: T                                                                     
        grads_dim: t                                                                
        long_name: time                                                             
        missing_value: -9999                                                        
                                                                                    
    depth:                                                                          
        axis: Z                                                                     
        col: depth                                                                  
        long_name: depth                                                            
        missing_value: -9999                                                        
        units: m                                                                    
                                                                                    
    temp:                                                                           
        col: temp                                                                   
        long_name: temperature                                                      
        missing_value: -9999                                                        
        units: degc

Note that you can have attributes that read from the database. They should be 
prefixed by the token ``!Query``.
""",
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
