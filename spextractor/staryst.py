

class Loop(StarBase):
    """
    Question: is the order of the rows important?
    Answer: for now, we'll go with 'no'
    """

    def __init__(self, keycols, restcols, rows):
        self.keycols = keycols
        self.restcols = restcols
        self.rows = {}
        num_keys = len(keycols)
        for r in rows:
            self.add_row(r[:num_keys], r[num_keys:])
    
    def _schema_check(self, keyvals, restvals):
        if len(keyvals) != len(self.keycols):
            raise ValueError('number of key values must match number of key columns')
        if len(restvals) != len(self.restcols):
            raise ValueError('number of rest values must match number of rest columns')
    
    def add_row(self, keyvals, restvals):
        self._schema_check(keyvals, restvals)
        if keyvals in self.rows:
            raise ValueError("can't have duplicate key values -- %s" % str(keyvals))
        self.rows[keyvals] = restvals
    
    def update_row(self, keyvals, restvals):
        """
        Loop -> [?] -> [?] -> [(?, ?)]
        set the restvals of a row, returning the changed columns
        """
        self._schema_check(keyvals, restvals)
        if keyvals not in self.rows:
            raise ValueError("can't update row -- key not found -- %s" % str(keyvals))
        # have to save this for later
        old_restvals = self.rows[keyvals]
        # next, update the row
        self.rows[keyvals] = restvals
        # figure out which columns changed
        return [(colname, old, new) for (colname, old, new) in zip(old_restvals, restvals, self.restcols) if old != new]
    
    def add_column(self, name, f):
        """
        f generates new values, based on the other values within the row
        """
        restcols.append(name)
        for (k, v) in self.rows.items():
            v.append(f(list(k) + v))
    
    def to_cst(self, prefix):
        keys = self.keycols + self.restcols
        idents = [prefix + '.' + k for k in keys]
        rows = []
        for (k, v) in sorted(self.rows.items(), key=lambda x: x[0]):
            rows.append(map(starcst.build_value(list(k) + v))
        return starcst.Loop(idents, rows)


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


class Data(StarBase):

    def __init__(self, name, saves):
        self.name = name
        self.saves = saves
    
    def to_cst(self):
        saves = dict([(name, s.to_cst(name)) for (name, s) in self.saves.items()])
        return starcst.Data(self.name, saves)

