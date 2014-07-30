

class StarBase(object):
    '''
    Provides meaningful defaults for:
     - equality
     - inequality
     - string representation
    
    Subclasses must provide:
     - toJSONObject :: StarBase -> Dict
    '''
    
    def __eq__(self, other):
        try:
            return self.__dict__ == other.__dict__
        except: # if the other object doesn't have a `__dict__` attribute, don't want to blow up 
            return False
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __repr__(self):
        return repr(self.toJSONObject())



class UQValue(StarBase):
    
    def __init__(self, value):
        specials = set('\n\r \t"#\'_')
        spaces = set('\n\r \t')
        # yes, there must be at least one character
        if value[0] in specials:
            raise ValueError("unquoted value can't start with special character")
        for c in value[1:]:
            if c in spaces:
                raise ValueError("unquoted value can't contain whitespace")
        self.value = value
    
    def toJSONObject(self):
        return {'type': 'UQValue', 'value': self.value}



class DQValue(StarBase):

    def __init__(self, value):
        if '\n' in value:
            raise ValueError("Double-quoted string can't contain newlines")
        self.value = value
    
    def toJSONObject(self):
        return {'type': 'DQValue', 'value': self.value}



class SCValue(StarBase):

    def __init__(self, value):
        if value.find('\n;') >= 0:
            raise ValueError("Semicolon-delimited string can't contain '\n;'")
        self.value = value
    
    def toJSONObject(self):
        return {'type': 'SCValue', 'value': self.value}



class Loop(StarBase):

    def __init__(self, keys, rows):
        if not isinstance(keys, list):
            raise TypeError('Loop needs list of keys')
        if len(keys) != len(set(keys)):
            raise ValueError('Loop requires unique keys')
        if not isinstance(rows, list):
            raise TypeError('Loop needs list of rows')
        for r in rows:
            if not isinstance(r, list):
                raise TypeError('Loop rows must be lists')
            if len(r) != len(keys):
                raise ValueError('Loop row: %i keys, but %i values' % (len(keys), len(r)))
        self.keys = keys
        self.rows = rows

    def toJSONObject(self):
        return {'type': 'Loop', 
                'keys': self.keys,
                'rows': self.rows}

    def getRowAsDict(self, rowIndex):
        return dict(zip(self.keys, self.rows[rowIndex]))


class Save(StarBase):

    def __init__(self, datums, loops):
        if not isinstance(datums, dict):
            raise TypeError('saveframe datums must be a dict')
        if not isinstance(loops, list):
            raise TypeError('saveframe loops must be a list')
        self.datums = datums
        self.loops = loops

    def toJSONObject(self):
        return {'type'  : 'Save', 
                'datums': self.datums, 
                'loops' : [l.toJSONObject() for l in self.loops]}


class Data(StarBase):

    def __init__(self, name, saves):
        self.name = name
        if not isinstance(saves, dict):
            raise TypeError(('save frames must be a dict', saves, type(saves)))
        self.saves = saves

    def toJSONObject(self):
        return {'type'       : 'Data', 
                'name'       : self.name, 
                'save frames': dict((k, s.toJSONObject()) for (k, s) in self.saves.items())}



def build_value(my_string):
    """
    String -> Error StarValue
    """
    if not isinstance(my_string, basestring):
        args = (repr(type(my_string)), my_string)
        raise TypeError('build_value requires a string -- got %s (%s)' % args)
    if '\n' not in my_string:
        return DQValue(my_string)
    if my_string.find('\n;') == -1:
        return SCValue(my_string)
    raise ValueError("unable to build NMR-Star value from <" + my_string + ">")
    


def dump_value(value):
    if isinstance(value, DQValue):
        return '"' + value.value + '"'
    elif isinstance(value, SCValue):
        return '\n;' + value.value + ';\n'
    elif isinstance(value, UQValue):
        return value.value
    else:
        raise ValueError("invalid NMR-Star value -- %s (%s)" % (repr(value), repr(type(value))))

def dump_loop(loop, log):
    log.append('    loop_\n')
    for k in loop.keys:
        log.append('      _' + k + '\n')
    log.append('\n')
    for row in loop.rows:
        log.append('      ')
        for val in row:
            log.append(dump_value(val) + ' ')
        log.append('\n')
    log.append('    stop_\n\n')

def dump_save(name, save, log):
    log.append('  save_' + name + '\n')
    for (key, value) in sorted(save.datums.items(), key=lambda x: x[0]):
        log.append('    _' + key + ' ' + dump_value(value) + '\n')
    log.append('\n')
    for loop in save.loops:
        dump_loop(loop, log)
    log.append('  save_\n\n\n')

def dump_data(data, log):
    log.append('data_' + data.name + "\n\n")
    for (name, save) in sorted(data.saves.items(), key=lambda x: x[0]):
        dump_save(name, save, log)

def dump(data):
    log = []
    dump_data(data, log)
    return ''.join(log)


def _row(*vals):
    return map(build_value, vals)

eg1 = Data('abc', 
           {'123': Save({'def': build_value('xyz'), 
                         'ghi': build_value('ab\ncd'),
                         'qrs': build_value('zomg')}, 
                        [Loop(['a', 'b'], [_row('1', '2'), _row('3', '4')]),
                         Loop(['c', 'd'], [_row('hi', 'bye'), _row('xor', 'blar'), _row('xy\nz', 'n1')])])})

my_string = dump(eg1)
