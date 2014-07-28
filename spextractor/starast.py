from . import starcst as cst


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
    
    def toJSONObject(self):
        return {
            'type': 'ALoop',
            'prefix': self.prefix,
            'keys': self.keys,
            'rows': self.rows
        }


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
    
    def toJSONObject(self):
        return {
            'type': 'ASave',
            'name': self.name,
            'category': self.category,
            'prefix': self.prefix,
            'datums': self.datums,
            'loops': [l.toJSONObject() for l in self.loops]
        }


class Data(cst.StarBase):
    """
    1. ?
    """
    
    def __init__(self, name, saves):
        self.name = name
        self.saves = saves

    def translate(self):
        return cst.Data(self.name, dict([(n, s.translate()) for (n, s) in self.saves.items()]))
    
    def toJSONObject(self):
        return {
            'type': 'AData',
            'name': self.name,
            'saves': dict([(k, v.toJSONObject()) for (k, v) in self.saves.items()])
        }
