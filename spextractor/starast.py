from .starcst import StarBase
from . import starcst



class Loop(StarBase):
    """
    Question: is the order of the rows important?
    Answer: for now, we'll go with 'no'
    """

    def __init__(self, keycols, restcols, rows):
        if len(set(keycols + restcols)) != len(keycols) + len(restcols):
            raise ValueError('duplicate column in Loop')
        self.keycols = list(keycols) # copy for safety
        self.restcols = list(restcols) # copy for safety
        self.rows = {}
        num_keys = len(keycols)
        for (k, v) in rows.items():
            self.add_row(k, v)
    
    def _schema_check(self, keyvals, restvals):
        if len(keyvals) != len(self.keycols):
            raise ValueError('number of key values must match number of key columns')
        if len(restvals) != len(self.restcols):
            args = (restvals, self.restcols)
            raise ValueError('number of rest values must match rest columns -- %s vs. %s' % args)
    
    def add_row(self, keyvals, restvals):
        self._schema_check(keyvals, restvals)
        pk = tuple(keyvals)
        if pk in self.rows:
            raise ValueError("can't have duplicate key values -- %s" % str(keyvals))
        self.rows[pk] = list(restvals) # make a copy for safety
    
    def update_row(self, keyvals, restvals):
        """
        Loop -> [?] -> [?] -> [(?, ?)]
        set the restvals of a row, returning the changed columns
        """
        self._schema_check(keyvals, restvals)
        pk = tuple(keyvals)
        if pk not in self.rows:
            raise ValueError("can't update row -- key not found -- %s" % str(keyvals))
        row = self.rows[pk]
        changes = []
        for (ix, colname) in enumerate(self.restcols, start=0):
            old, new = row[ix], restvals[ix]
            if new != old:
                changes.append({'column': colname, 'old_value': old, 'new_value': new})
                row[ix] = new
        return changes
    
    def update_column(self, keyvals, column, value):
        """
        set a non-key column of a row
        possible errors:
         1. keys don't match Loop schema (wrong number of keys)
         2. row not found, based on keyvals
         3. column not found in restcols
        """
        if len(keyvals) != len(self.keycols):
            # error 1
            raise ValueError('number of key values must match number of key columns')
        pk = tuple(keyvals)
        # error 2
        row = self.rows[pk]
        # error 3
        index = self.restcols.index(column)
        row[index] = value
    
    def get_column(self, keyvals, column):
        if len(keyvals) != len(self.keycols):
            # error 1
            raise ValueError('number of key values must match number of key columns')
        pk = tuple(keyvals)
        # error 2
        row = self.rows[pk]
        # error 3
        index = self.restcols.index(column)
        return row[index]
    
    def add_column(self, name, init_value='.'):
        """
        """
        keys = self.keycols + self.restcols
        if name in keys:
            raise ValueError('duplicate column name -- %s in %s' % (name, keys))
        self.restcols.append(name)
        for (k, v) in self.rows.items():
            v.append(init_value)
    
    def to_cst(self, prefix):
        keys = self.keycols + self.restcols
        idents = [prefix + '.' + k for k in keys]
        rows = []
        def f(x):
            key = x[0]
            fst = key[0]
            try:
                return int(fst)
            except:
                return fst
        for (k, v) in sorted(self.rows.items(), key=f):
            rows.append(map(starcst.build_value, list(k) + v))
        return starcst.Loop(idents, rows)
    
    def toJSONObject(self):
        return {
            'type'      : 'Loop',
            'keycols'   : self.keycols,
            'restcols'  : self.restcols,
            'rows'      : self.rows
        }


class Save(StarBase):

    def __init__(self, category, prefix, datums, loops):
        self.category = category
        self.prefix = prefix
        for (k, v) in datums.items():
            if k in ['Sf_framecode', 'Sf_category']:
                raise ValueError('illegal key in SaveFrame -- %s' % k)
        self.datums = datums
        if not isinstance(loops, dict):
            raise TypeError('expected dict for loops -- got %s' % repr(type(loops)))
        self.loops = loops
    
    def to_cst(self, name):
        datums = {'Sf_framecode': name, 'Sf_category': self.category}
        for (k, v) in self.datums.items():
            datums[k] = v
        pre_datums = dict([(self.prefix + '.' + k, starcst.build_value(v)) for (k, v) in datums.items()])
        loops = [loop.to_cst(loopname) for (loopname, loop) in self.loops.items()]
        return starcst.Save(pre_datums, loops)
    
    def toJSONObject(self):
        return {
            'type'      : 'Save',
            'category'  : self.category,
            'prefix'    : self.prefix,
            'datums'    : self.datums,
            'loops'     : dict([(k, v.toJSONObject()) for (k,v) in self.loops.items()])
        }


class Data(StarBase):

    def __init__(self, name, saves):
        self.name = name
        self.saves = saves
    
    def to_cst(self):
        saves = dict([(name, s.to_cst(name)) for (name, s) in self.saves.items()])
        return starcst.Data(self.name, saves)
    
    def toJSONObject(self):
        return {
            'type'  : 'Data',
            'name'  : self.name,
            'saves' : dict([(k, v.toJSONObject()) for (k,v) in self.saves.items()])
        }



l = Loop(['a', 'b'], ['c', 'd', 'Tag_row_ID'], 
         {('1', '2'): ['3', '4', '200'],
          ('1', '3'): ['8', '8', '210']})
l2 = Loop(['a', 'b'], ['c', 'd', 'Tag_row_ID'], 
          {('1', '2'): ['3', '5', '.'],
           ('1', '3'): ['7', '7', '.'],
           ('1', '4'): ['2', '5', '.']})
