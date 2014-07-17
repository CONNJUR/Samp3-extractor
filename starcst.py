

class Base(object):
    '''
    Provides default:
     - equality
     - inequality
     - meaningful string representation 
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


class DQValue(Base):

    def __init__(self, value):
        if '\n' in value:
            raise ValueError("Double-quoted string can't contain newlines")
        self.value = value
    
    def toJSONObject(self):
        return {'type': 'DQValue', 'value': self.value}

class SCValue(Base):

    def __init__(self, value):
        if value.find('\n;') >= 0:
            raise ValueError("Semicolon-delimited string can't contain '\n;'")
        self.value = value
    
    def toJSONObject(self):
        return {'type': 'SCValue', 'value': self.value}

def build_value(my_string):
    if '\n' not in my_string:
        return SQValue(my_string)
    if value.find('\n;') == -1:
        return SCValue(value)
    raise ValueError("unable to build NMR-Star value from <" + my_string + ">")
    


class Loop(Base):

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


class Save(Base):

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


class Data(Base):

    def __init__(self, name, saves):
        self.name = name
        if not isinstance(saves, dict):
            raise TypeError(('save frames must be a dict', saves, type(saves)))
        self.saves = saves

    def toJSONObject(self):
        return {'type'       : 'Data', 
                'name'       : self.name, 
                'save frames': dict((k, s.toJSONObject()) for (k, s) in self.saves.items())}



def dump_value(value, log):
    if isinstance(value, DQValue):
        log.append('"' + value.value + '"')
    elif isinstance(value, SCValue):
        log.append('\n;' + value.value + ';\n')
    else:
        raise ValueError("invalid NMR-Star value -- %s" % repr(value))

def dump_loop(loop, log):
    log.append('    loop_\n')
    for k in loop.keys:
        log.append('      _' + key + '\n')
    log.append('\n')
    for row in loop.rows:
        log.append('      ')
        for val in row:
            log.append(dump_value(val, log) + ' ')
        log.append('\n')
    log.append('    stop_\n')

def dump_save(name, save, log):
    log.append('  save_' + name + '\n')
    for (key, value) in sorted(save.datums.items(), key=lambda x: x[0]):
        log.append('    _' + key + ' ' + dump_value(value) + '\n')
    log.append('\n')
    for loop in save.loops:
        dump_loop(loop, log)

def dump_data(data, log):
    log.append('data_' + data.name + "\n\n")
    for (name, save) in sorted(data.saves.items(), key=lambda x: x[0]):
        dump_save(name, save, log)

def dump(data):
    log = []
    dump_data(data, log)
    return ''.join(log)
