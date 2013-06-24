database: 
    dsn: 'sqlite:///simple.db'
    table: test

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

sequence:
    name: simple
    items: !Query 'SELECT COUNT(id) FROM test'

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
    type: Float32
    global_range: [-180, 180]
    valid_range: !Query 'SELECT min(lon), max(lon) FROM test'

lat:
    col: lat
    axis: Y
    grads_dim: y
    long_name: latitude
    units: degrees_north
    missing_value: -9999
    type: Float32
    global_range: [-90, 90]
    valid_range: !Query 'SELECT min(lat), max(lat) FROM test'

time:
    col: time
    axis: T
    grads_dim: t
    long_name: time
    missing_value: -9999
    type: String

depth: 
    axis: Z
    col: depth
    long_name: depth
    missing_value: -9999
    type: Float32
    units: m

temp:
    col: temp
    long_name: temperature
    missing_value: -9999
    type: Float32
    units: degc
