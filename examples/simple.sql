# please read http://groups.google.com/group/pydap/browse_thread/thread/c7f5c569d661f7f9 before 
# setting your password on the DSN
[database]
dsn = "sqlite:///simple.db"
table = "test"

[dataset]
name = "test_dataset"
owner = "Roberto De Almeida"
contact = "roberto@dealmeida.net"
version = 1.0

    [[NC_GLOBAL]]
    history = "Created by the Pydap SQL handler"

[_id]
col = "id"
long_name = "sequence id"
missing_value = -9999

[lon]
col = "lon"
type = "Float32"
units = "degree_north"
long_name = "longitude"
missing_value = -9999
axis = "X"
valid_range = [-180.0, 180.0]

[lat]
col = "lat"
type = "Float32"
units = "degree_east"
long_name = "latitude"
missing_value = -9999
axis = "Y"

[time]
col = "time"
#type = "Float64"
#units = "days since 1978-3-1"
#units = "hours since 1997-1-1"
type = 'String'
long_name = "time"
missing_value = -9999
axis = "T"

[depth]
col = "depth"
type = "Float32"
units = "m"
long_name = "depth"
missing_value = -9999
axis = "Z"

[temp]
col = "temp"
type = "Float32"
units = "degc"
long_name = "temperature"
missing_value = -9999
