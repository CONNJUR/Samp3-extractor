from . import dump2star
from . import staryst
from . import starast
from . import starcst


loop_keys = {
    # Peaks save frame
    'Peak'                      : ['ID']                        ,
    'Peak_char'                 : ['Peak_ID', 'Spectral_dim_ID'],   # frequency
    'Peak_general_char'         : ['Peak_ID']                   ,   # height
    'Assigned_peak_chem_shift'  : ['Peak_ID', 'Spectral_dim_ID'],
    # Resonances save frame
    'Resonance'                 : ['ID']                        ,
    #'Resonance_assignment'     : ['???']                       ,
    'Spin_system'               : ['ID']                        ,
    'Spin_system_link'          : ['From_spin_system', 'To_spin_system'],
    'Spectral_dim': ['ID']
    # TODO what about GSS typing and GSS-residue?
}

loops_yes = set([
    'Peak', 'Peak_char', 'Peak_general_char', 'Assigned_peak_chem_shift',
    'Resonance', 'Spin_system', 'Spin_system_link'])
loops_no = set(['Spectral_dim'])


def build_loop(aloop):
    pre = aloop.prefix
    keys = loop_keys[pre]
    n = len(keys)
    if keys != aloop.keys[:n]:
        raise ValueError('expected key columns at beginning of Loop keys -- %s, %s' % (pre, aloop.keys))
    restcols = aloop.keys[n:]
    rows = {}
    for r in aloop.rows:
        pk, rest = tuple(r[:n]), r[n:]
        if pk in rows:
            raise ValueError('duplicate pk in Loop %s -- %s' % (pre, pk))
        rows[pk] = rest
    return staryst.Loop(keys, restcols, rows)


def build_save(asave):
    loops = {}
    for l in asave.loops:
        if l.prefix in loops:
            raise ValueError('duplicate loop prefix -- %s' % l.prefix)
        loops[l.prefix] = build_loop(l)
    return staryst.Save(asave.category, asave.prefix, asave.datums, loops)    


def build_data(adata):
    saves = dict([(name, build_save(asave)) for (name, asave) in adata.saves.items()])
    return staryst.Data(adata.name, saves)


def from_ast(adata):
    """
    convert a STAR AST to an NMRSTAR AST -- implemented in the staryst module
    """
    return build_data(adata)


"""
1. compare two NMR-Star ASTs, and find the differences in the loop tables
 - new rows
 - changed rows -- although not knowing the PKs of each loop table,
   this may end up being deleted + added rows
"""


def diff_loop(l1, l2, diff_counter, ignore_keys=['Tag_row_ID']):
    """
    merge l2 into l1, modifying l1
    return a list of all changes -- 1 element per changed column 
      i.e. there may be multiple changed columns in a single row
      in the form of `[(String, String, String)]`
    """
    l = [l1.keycols, l1.restcols]
    r = [l2.keycols, l2.restcols]
    changes = []
    new = []
    if l != r:
        raise ValueError('invalid loop comparison -- %s and %s' % (l, r))
    for (pk, rest) in l2.rows.items():
        # a new row!
        if pk not in l1.rows:
            l1.add_row(pk, rest)
            diff_id = diff_counter
            l1.update_column(pk, 'Tag_row_ID', str(diff_id))
            diff_counter += 1
            new.append(diff_id)
            continue
        # (possibly) modifying an existing row
        old_diff_id = l1.get_column(pk, 'Tag_row_ID')
        full_diff = l1.update_row(pk, rest)
        l1.update_column(pk, 'Tag_row_ID', old_diff_id) # HACK don't let Tag_row_ID be changed ... yet!
        diff = [r for r in full_diff if r['column'] not in ignore_keys]
#        print 'diff: ', diff
        if diff == []:
            continue
        diff_id = diff_counter
        diff_counter += 1
        l1.update_column(pk, 'Tag_row_ID', str(diff_id))
        changes.append({'old_row_id': old_diff_id, 'new_row_id': str(diff_id), 'diff': diff})
    return (diff_counter, changes, new)


def diff_save(s1, s2, diff_counter):
    """
    merge s2 into s1, modifying s1
    """
    l = [s1.category, s1.prefix]
    r = [s2.category, s2.prefix]
    if l != r:
        raise ValueError('invalid save comparison -- %s and %s' % (l, r))
    # ignore the rest of the datums
    changes, new = [], []
    for pre in set(s1.loops.keys() + s2.loops.keys()):
        if pre not in s1.loops or pre not in s2.loops:
            raise ValueError('loop name %s missing from save frame' % pre)
        if pre in loops_yes:
            diff_counter, loop_changes, loop_new = diff_loop(s1.loops[pre], s2.loops[pre], diff_counter)
            changes.extend(loop_changes)
            new.extend(loop_new)
        elif pre in loops_no:
            continue
        else:
            raise ValueError('unrecognized loop prefix -- %s' % pre)
    return (diff_counter, changes, new)


def diff_data(d1, d2, diff_counter):
    """
    merges d2 into d1, based on matching:
      1. save frame names
      2. loop names
      3. loop rows by values of key columns
    thus, d1 is modified (d2 is not) in two ways
      1. "vanilla" NMR-STAR save frames, loops, etc. are changed
      2. the new annotations save frame is *only* augmented
    """
    changes, new = [], []
    for name in set(d1.saves.keys() + d2.saves.keys()):
        if name == 'my_annotations':
            continue
        if name not in d1.saves or name not in d2.saves:
            raise ValueError('save name %s missing from data block' % name)
        diff_counter, save_changes, save_new = diff_save(d1.saves[name], d2.saves[name], diff_counter)
        changes.extend(save_changes)
        new.extend(save_new)
    return (diff_counter, changes, new)


def diff_many(ds, diff_counter=1, tag_counter=1):
    """
    let's have the first d be a dummy one -- a bunch of empty loops with no rows in them
    """
    tag_changes = {}
    changes, new = [], []
    base = ds[0] # yes, we're assuming that there's always at least 1
    for d in ds[1:]:
        diffs = {'new': [], 'changes': []}
        tag_changes[tag_counter] = diffs
        diff_counter, data_changes, data_new = diff_data(base, d, diff_counter)
        diffs['changes'].extend(data_changes)
        diffs['new'].extend(data_new)
         # if there's no changes -- no problem, still want to increment the tag counter
        tag_counter += 1
    return {
        'diff_counter'  : diff_counter  ,
        'changes'       : tag_changes
    }


def annotations(ds):
    second_tag_id = 1
    diff = diff_many(ds, tag_counter=second_tag_id)
    first = ds[0]
    tags = staryst.Loop(['ID'], 
                        ['Previous_tag_ID', 'Author', 'Entry_ID', 'Annotation_list_ID', 'Detail'],
                        {})
    tag_rows = staryst.Loop(['ID'], 
                            ['Previous_tag_row_ID', 'Tag_ID', 'Entry_ID', 'Annotation_list_ID'],
                            {})
    tag_diffs = staryst.Loop(['ID'],
                             ['Tag_row_ID', 'Entry_ID', 'Annotation_list_ID', 'Column_name', 'Previous_value'],
                             {})
    sf_id= '1'
    datums = {
        'Entry_ID': '888888',
        'ID': sf_id
    }
    loops = {
        'Tag'       : tags      ,
        'Tag_row'   : tag_rows  ,
        'Tag_diff'  : tag_diffs
    }
    first.saves['my_annotations'] = staryst.Save('annotations', 'Annotation_list', datums, loops)
    tags.add_row([str(second_tag_id - 1)], ['.', '.', '888888', sf_id, '.'])
    tag_diff_id = 1
    for (tag_id, chs) in sorted(diff['changes'].items(), key=lambda x: int(x[0])):
        tag = str(tag_id)
        tags.add_row([tag], [str(tag_id - 1), '.', '888888', sf_id, '.'])
        for c in chs['changes']:
            old, new = c['old_row_id'], c['new_row_id']
            tag_rows.add_row([new], [old, tag, '888888', sf_id])
            for d in c['diff']:
                tag_diffs.add_row([str(tag_diff_id)], 
                                  [new, '888888', sf_id, d['column'], d['old_value']])
                tag_diff_id += 1
        for n in chs['new']:
            tag_rows.add_row([str(n)], ['.', tag, '888888', sf_id])
            tag_diffs.add_row([str(tag_diff_id)], [str(n), '888888', sf_id, '.', '.'])
            tag_diff_id += 1
    return first


def run(high=4):
    """
    create NMR-Star files from each of the JSON files
    """
    import json
    datas = []
    paths = ['json_' + str(ix) + '.txt' for ix in range(1, high + 1)]

    for path in paths:
        with open(path, 'r') as my_file:
            data = json.loads(my_file.read())
            extracted_saves = dump2star.extract_spectra('888888', data)
            data_block = starast.Data('888888', extracted_saves)
            yst = from_ast(data_block)
            datas.append(yst)

    done = annotations(datas)
    with open('my_final', 'w') as out:
        out.write(starcst.dump(done.to_cst()))
    return done
#    for d in datas:
#        print d, '\n\n\n'
#    (_, changes, new) = diff_many(datas, 1, 1)
#    first = datas[0]
#    with open('my_final', 'w') as out:
#        out.write(starcst.dump(first.to_cst()))
#    for c in changes:
#        print c
#    for n in new:
#        print n


out = run()


def example():
    y0 = staryst.Data('abc',
                      {'def': staryst.Save('456', '789', {},
                                           {'Spin_system': staryst.Loop(['ID'], 
                                                                        ['b', 'c', 'Tag_row_ID'], {})})})
    eg_loops = [
        starast.Loop('Spin_system', ['ID', 'b', 'c', 'Tag_row_ID'],
                     [['1', '2', '3', '.'], ['2', '20', '44', '.'], ['3', '18', '27', '.']])
    ]
    eg1 = starast.Data('abc',
                       {'def': starast.Save('123', '456', '789', {}, eg_loops)})
    y1 = from_ast(eg1)
    y2 = staryst.Data('abc',
                 {'def': staryst.Save('456', '789', {},
                                      {'Spin_system': staryst.Loop(['ID'], ['b', 'c', 'Tag_row_ID'], 
                                                                   {('1',): ['2', '3', '?'], 
                                                                    ('2',): ['20', '45', '.'],
                                                                    ('3',): ['19', '28', '.'],
                                                                    ('4',): ['77', '7', '?']})})})

    out = annotations([y0, y1, y2])
    print starcst.dump(y0.to_cst()) # same as `out.to_cst()`?

# example()
