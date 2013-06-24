pydap.handlers.sql
==================

This handler allows Pydap to server data from any relational database supported
by [SQLAlchemy](http://www.sqlalchemy.org/). Each dataset is represented by a
YAML file (with extension `.sql`) that defines the database connection,
variables and other associated metadata. Here's a simple example:

```yaml
# These parameters are mandatory; they define the database to connect and the
# table holding the data. Note that table might be a selection.
database:
    dsn: 'sqlite:///simple.db'
    table: test

# This is just metadata defining the dataset; no attributes are required.
dataset:
    NC_GLOBAL:
        history: Created by the Pydap SQL handler

    contact: roberto@dealmeida.net
    name: test_dataset
    owner: Roberto De Almeida
    version: 1.0
    last_modified: !Query 'SELECT time FROM test ORDER BY time DESC LIMIT 1;'

# This is just metadata defining the sequence; no attributes are required.
sequence:
    name: simple
    items: !Query 'SELECT COUNT(id) FROM test'

# Each variable must have an attribute called `col`, referencing the column;
# all other are optional.
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
```

Note that you can have attributes that read from the database. They should be 
prefixed by the token `!Query`.
