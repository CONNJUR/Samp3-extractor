from . import starcst as cst


class Save(cst.StarBase):
    """
    1. Sf_framecode === name of save frame
    2. Sf_category === link to NMR-Star dictionary defining the schema
    3. prefix of keys in key/val pairs -- can be found in NMR-Star dictionary
    """

    def __init__(self, name, category, prefix, datums, loops):
        self.name = name
        self.category = category
        self.prefix = prefix
        for k in datums.keys():
            if k in ['Sf_framecode', 'Sf_category']:
                raise ValueError('illegal key -- %s' % k)
        self.datums = datums
        self.loops = loops
    
    def translate(self):
        """
        Save[AST] -> Save[CST]
        """
        prefix = self.prefix
        datums = dict([(prefix + '.' + k, cst.build_value(v)) for (k, v) in self.datums.items()])
        datums[prefix + '.Sf_framecode'] = cst.build_value(self.name)
        datums[prefix + '.Sf_category'] = cst.build_value(self.category)
        loops = [l.translate() for l in self.loops]
        # TODO what about the name (i.e. save_blahblah?)
        return cst.Save(datums, loops)


class Loop(cst.StarBase):
    """
    1. prefix of keys
    2. convert Strings to NMR-Star values
    """
    
    def __init__(self, prefix, keys, rows):
        self.prefix = prefix
        self.keys = keys
        self.rows = rows
    
    def translate(self):
        keys = [self.prefix + '.' + k for k in self.keys]
        rows = [map(cst.build_value, row) for row in self.rows]
        return cst.Loop(keys, rows)


class Data(cst.StarBase):
    """
    ?
    """
    def __init__(self):
        raise ValueError('unimplemented')
    
    def translate(self):
        raise ValueError('unimplemented')

