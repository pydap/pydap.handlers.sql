import sys
import re 
import os.path
import operator
import itertools
import copy
import time
from email.utils import formatdate
from threading import RLock
from datetime import datetime
import logging
log = logging.getLogger('pydap')

import yaml
from configobj import ConfigObj, ConfigObjError
from sqlalchemy import create_engine

from pydap.model import *
from pydap.model import SequenceData
from pydap.proxy import ConstraintExpression
from pydap.lib import combine_slices, fix_slice
from pydap.util.safeeval import expr_eval
from pydap.handlers.lib import BaseHandler
from pydap.exceptions import OpenFileError, ConstraintExpressionError


# connection pool
DBPOOL = {}
DBLOCK = RLock()


class Handler(BaseHandler):

    extensions = re.compile(r"^.*\.sql$", re.IGNORECASE)

    def __init__(self, filepath):
        self.filepath = filepath

    def parse_constraints(self, environ):
        try:
            try:
                config = ConfigObj(self.filepath, unrepr=True)
            except ConfigObjError:
                yaml.add_constructor('!Query', yaml_query)
                with open(self.filepath) as fp:
                    config = yaml.load(fp)
        except Exception, e:
            message = 'Unable to open file %s. %s' % (self.filepath, e)
            raise OpenFileError(message)

        dsn = config['database']['dsn']
        with DBLOCK:
            if dsn not in DBPOOL:
                DBPOOL[dsn] = create_engine(dsn)

        # Build the dataset object, populating the metadata from the 
        # config file.
        attrs = config.get('dataset', {}).copy()
        if 'last_modified' in attrs:
            last_modified = attrs['last_modified'][0]
            if isinstance(last_modified, basestring):
                last_modified = datetime.strptime(last_modified, '%Y-%d-%m %H:%M:%S')
            last_modified = formatdate( time.mktime( last_modified.timetuple() ) )
            attrs['last_modified'] = last_modified
            environ['pydap.headers'].append( ('Last-modified', last_modified) )
        name = attrs.pop('name', os.path.split(self.filepath)[1])
        dataset = DatasetType(name, attrs)

        # Build the sequence object, and insert it in the dataset.
        attrs = config.get('sequence', {}).copy()
        name = attrs.pop('name', 'sequence')
        seq = SequenceType(name, attrs)
        dataset[seq.name] = seq

        # Parse the constraint expression from ``environ['pydap.ce']``,
        # extracting the requested fields, any filters (queries) and the
        # slice for the sequence.
        fields, queries = environ['pydap.ce']
        queries = filter(bool, queries)  # fix for older version of pydap
        all_vars = [section for section in config 
                if section not in ['database', 'dataset', 'sequence']]
        slices = [f[0][1] for f in fields if f[0][0] == seq.name]
        if slices:
            slice_ = slices[0]
        else:
            slice_ = None
        # Check that all slices are equal. 
        if [s for s in slices if s != slice_]:
            raise ConstraintExpressionError('Slices are not unique!')
        # If no fields have been explicitly requested, of if the sequence
        # has been requested directly, return all variables.
        if not fields or seq.name in [f[0][0] for f in fields if len(f) == 1]:
            fields = [[(name, ())] for name in all_vars]

        # Add all requested variables to the sequence.
        cols = []
        for var in fields:
            while var:
                name, unused_slice = var.pop(0)
                if name == seq.name:
                    continue
                elif name in all_vars:
                    attrs = config[name].copy()
                    cols.append(attrs.pop('col'))
                    type_ = typemap[attrs.pop('type', 'Int32').lower()]
                    seq[name] = BaseType(name=name, type=type_, attributes=attrs)
                else:
                    raise ConstraintExpressionError('Invalid token: "%s"' % name)

        # Add a proxy to the data.
        seq.data = SQLProxy(seq.id, tuple(cols), queries, config, slice_)
        return dataset


class SQLProxy(SequenceData):
    """
    A ``SequenceData`` object that reads data from a database.

    """
    def __init__(self, id, cols, queries, config, slice_=None):
        self.id = id
        self.cols = cols
        self.queries = queries
        self.config = config
        self._slice = slice_ or (slice(None),)

        try:
            name = config['sequence']['name']
        except KeyError:
            name = 'sequence'
        # map id to col name
        self.mapping = dict([
            ('%s.%s' % (name, section), config[section]['col'])
            for section in config
            if section not in ['database', 'dataset', 'sequence']])

    def __deepcopy__(self, memo=None, _nil=[]):
        out = self.__class__(self.id, self.cols[:],
                self.queries[:], self.config, 
                self._slice)
        return out

    def __getitem__(self, key):
        out = copy.deepcopy(self)
        if isinstance(key, ConstraintExpression):
            out.queries.extend(str(key).split('&'))
        elif isinstance(key, basestring):
            out._slice = (slice(None),)
            out.id = '%s.%s' % (self.id, key)
            out.cols = self.mapping[out.id]
        elif isinstance(key, tuple):
            out.cols = tuple( self.mapping['%s.%s' % (self.id, col)]
                    for col in key )
        else:
            out._slice = combine_slices(self._slice, fix_slice(key, (sys.maxint,)))
        return out

    def __len__(self):
        condition = parse_queries(self.queries, self.mapping)
        table = self.config['database']['table']
        offset = self._slice[0].start or 0
        limit = (self._slice[0].stop or sys.maxint) - (self._slice[0].start or 0)
        query = """SELECT COUNT(*)
FROM %(table)s
%(condition)s
LIMIT %(limit)d
OFFSET %(offset)d""" % locals()
        conn = DBPOOL[self.config['database']['dsn']].connect()
        log.info(query)
        results = conn.execute(query).fetchone()[0]
        conn.close()
        slice_ = fix_slice(self._slice, (results,))
        return (min(results, slice_[0].stop)-slice_[0].start-1)//slice_[0].step+1

    @property
    def query(self):
        if isinstance(self.cols, tuple):
            cols = ', '.join(self.cols)
        else:
            cols = self.cols
        condition = parse_queries(self.queries, self.mapping)
        table = self.config['database']['table']
        order = self.config['database'].get('id', 'id')
        offset = self._slice[0].start or 0
        limit = (self._slice[0].stop or sys.maxint) - (self._slice[0].start or 0)

        return """SELECT %(cols)s
FROM %(table)s
%(condition)s 
ORDER BY %(order)s
LIMIT %(limit)d
OFFSET %(offset)d""" % locals()

    def __iter__(self):
        conn = DBPOOL[self.config['database']['dsn']].connect()
        log.info(self.query)
        data = conn.execute(self.query)

        # slice and filter data
        data = itertools.islice(data, 0, None, self._slice[0].step)
        if not isinstance(self.cols, tuple):
            data = itertools.imap(operator.itemgetter(0), data)

        for record in data:
            yield record
        conn.close()

    # Comparisons return a ``ConstraintExpression`` object
    def __eq__(self, other): return ConstraintExpression('%s=%s' % (self.id, other))
    def __ne__(self, other): return ConstraintExpression('%s!=%s' % (self.id, other))
    def __ge__(self, other): return ConstraintExpression('%s>=%s' % (self.id, other))
    def __le__(self, other): return ConstraintExpression('%s<=%s' % (self.id, other))
    def __gt__(self, other): return ConstraintExpression('%s>%s' % (self.id, other))
    def __lt__(self, other): return ConstraintExpression('%s<%s' % (self.id, other))


def parse_queries(queries, mapping):
    CE = re.compile(r'''^                         # Start of selection
                       (?P<var1>.*?)              # Anything
                       (?P<op><=|>=|!=|=~|>|<|=)  # Operators
                       {?                         # {
                       (?P<var2>.*?)              # Anything
                       }?                         # }
                       $                          # EOL
                    ''', re.VERBOSE)
    out = []
    for query in queries:
        m = CE.match(query)
        if not m:
            raise ConstraintExpressionError('Invalid constraint expression: %s.' % query)
        var1, op, var2 = m.groups()
        if op == '=~':
            raise ConstraintExpressionError('Regular expressions disallowed!')

        # evaluate variables
        if var1 in mapping:
            col = mapping[var1]
            var2 = expr_eval(var2)

            if isinstance(var2, tuple):
                subsubquery = []
                for var in var2:
                    subsubquery.append('(%s %s %s)' % (col, op, repr(var)))
                subquery = '(%s)' % ' OR '.join(subsubquery)
            else:
                subquery = '(%s %s %s)' % (col, op, repr(var2))
            out.append(subquery)
    condition = ' AND '.join(out)
    if condition:
        condition = 'WHERE %s' % condition
    return condition


def yaml_query(loader, node):
    # read DSN
    for obj in [obj for obj in loader.constructed_objects if isinstance(obj, yaml.MappingNode)]:
        try:
            mapping = loader.construct_mapping(obj)
            dsn = mapping['dsn']
            break
        except:
            pass

    # get/set connection
    with DBLOCK:
        if dsn not in DBPOOL:
            DBPOOL[dsn] = create_engine(dsn)
    conn = DBPOOL[dsn].connect()

    query = loader.construct_scalar(node)
    log.info(query)
    results = conn.execute(query).fetchone()
    conn.close()
    return results


if __name__ == '__main__':
    import sys
    import logging
    logging.basicConfig(stream=sys.stdout)
    logger = logging.getLogger('pydap')
    logger.setLevel(logging.INFO)

    from paste.httpserver import serve

    application = Handler(sys.argv[1])
    serve(application, port=8001)
