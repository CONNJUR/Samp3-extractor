from . import dump2star
from .starast import Loop, Save, Data
from . import starcst
import json



loops_yes = set([
    'Peak', 'Peak_char', 'Peak_general_char', 'Assigned_peak_chem_shift',
    'Resonance', 'Spin_system', 'Spin_system_link', 'Resonance_assignment'])
loops_no = set(['Spectral_dim'])


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
        if pre not in s2.loops:
            raise ValueError('loop name %s missing from save frame' % pre)
        if pre in loops_yes:
            if pre not in s1.loops:
                old = s2.loops[pre]
                s1.loops[pre] = Loop(old.keycols, old.restcols, {})
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
        if name not in d2.saves: # or name not in d2.saves:
            print d1.saves.keys(), len(str(d1))
            print d2.saves.keys(), len(str(d2))
#            print 'oops, missing %s' % name
#            continue
            raise ValueError('save name %s missing from data block' % name)
        if name not in d1.saves:
            old = d2.saves[name]
            d1.saves[name] = Save(old.category, old.prefix, old.datums, {})
        diff_counter, save_changes, save_new = diff_save(d1.saves[name], d2.saves[name], diff_counter)
        for s in save_changes:
            s['sf_name'] = name
        changes.extend(save_changes)
        new.extend([{'row_id': sn, 'sf_name': name} for sn in save_new])
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
    tags = Loop(['ID'], 
                ['Previous_tag_ID', 'Author', 'Detail'],
                {})
    tag_rows = Loop(['ID'], 
                    ['Previous_tag_row_ID', 'Tag_ID', 'Link_sf_framecode'],
                    {})
    tag_diffs = Loop(['ID'],
                     ['Tag_row_ID', 'Column_name', 'Previous_value'],
                     {})
    datums = {
        'ID': '1'
    }
    loops = {
        'Tag'       : tags      ,
        'Tag_row'   : tag_rows  ,
        'Tag_diff'  : tag_diffs
    }
    first.saves['my_annotations'] = Save('annotations', 'Annotation_list', datums, loops)
    tags.add_row([str(second_tag_id - 1)], ['.', '.', '.'])
    tag_diff_id = 1
    for (tag_id, chs) in sorted(diff['changes'].items(), key=lambda x: int(x[0])):
        tag = str(tag_id)
        tags.add_row([tag], [str(tag_id - 1), '.', '.'])
        for c in chs['changes']:
            old, new, sf_name = c['old_row_id'], c['new_row_id'], c['sf_name']
            tag_rows.add_row([new], [old, tag, sf_name])
            for d in c['diff']:
                tag_diffs.add_row([str(tag_diff_id)], 
                                  [new, d['column'], d['old_value']])
                tag_diff_id += 1
        for n in chs['new']:
            row_id = str(n['row_id'])
            sf_name = n['sf_name']
            tag_rows.add_row([row_id], ['.', tag, sf_name])
            tag_diffs.add_row([str(tag_diff_id)], [row_id, '.', '.'])
            tag_diff_id += 1
    return first


def add_boilerplate(yst_data):
    """
     1. add Entry_ID key to each saveframe
     2. add Entry_ID key to each loop, modifying each row
     3. for each save frame, take the `<prefix>.ID` key/val,
        and add a `<prefix>_ID` key to each contained loop with the same val
     
     this modifies the incoming data
    """
    entry_id = yst_data.name
    # 1.
    for (s_name, save) in yst_data.saves.items():
        if 'Entry_ID' in save.datums:
            raise ValueError('found Entry_ID already in save frame -- %s' % s_name)
        save.datums['Entry_ID'] = entry_id
        s_id = save.datums['ID']
        pre = save.prefix
        id_key = pre + '_ID'
        # 2. and 3.
        for (_, loop) in save.loops.items():
            loop.add_column('Entry_ID', init_value=entry_id)
            loop.add_column(id_key, init_value=s_id)


def run(paths):
    """
    create NMR-Star files from each of the JSON files
    """
    datas = []

    for path in paths:
        with open(path, 'r') as my_file:
            json_data = json.loads(my_file.read())
            datas.append(dump2star.extract(json_data, 'NEED_ACC_NUM'))

    done = annotations(datas)
    add_boilerplate(done)
    return done


def example():
    y0 = Data('abc',
              {'def': Save('456', '789', {},
                           {'Spin_system': Loop(['ID'], 
                                                ['b', 'c', 'Tag_row_ID'], {})})})
    eg_loops = [
        Loop('Spin_system', ['ID', 'b', 'c', 'Tag_row_ID'],
             [['1', '2', '3', '.'], ['2', '20', '44', '.'], ['3', '18', '27', '.']])
    ]
    y1 = Data('abc',
              {'def': Save('123', '456', '789', {}, eg_loops)})
    y2 = Data('abc',
              {'def': Save('456', '789', {},
                           {'Spin_system': Loop(['ID'], ['b', 'c', 'Tag_row_ID'], 
                                                {('1',): ['2', '3', '?'], 
                                                ('2',): ['20', '45', '.'],
                                                ('3',): ['19', '28', '.'],
                                                ('4',): ['77', '7', '?']})})})

    out = annotations([y0, y1, y2])
    print starcst.dump(y0.to_cst()) # same as `out.to_cst()`?

# example()


def get_name(dirname, ix):
    return ''.join([dirname, '/a', str(ix), '.txt'])


if __name__ == "__main__":
    import sys
    dirname, high = sys.argv[1], int(sys.argv[2])
    paths = [get_name(dirname, ix) for ix in range(1, high + 1)]
    paths.reverse()
    out = run(paths)
    print starcst.dump(out.to_cst())


