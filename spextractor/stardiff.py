from . import dump2star
from . import staryst


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
            l1.update_column(pk, 'Tag_row_ID', diff_id)
            diff_counter += 1
            new.append(diff_id)
            continue
        # (possibly) modifying an existing row
        old_diff_id = l1.get_column(pk, 'Tag_row_ID')
        full_diff = l1.update_row(pk, rest)
        diff = [r for r in full_diff if r[0] not in ignore_keys]
        print 'diff: ', diff
        if diff == []:
            continue
        diff_id = diff_counter
        diff_counter += 1
        l1.update_column(pk, 'Tag_row_ID', diff_id)
        changes.append((old_diff_id, diff_id, diff))
    return (diff_counter, changes, new)

loops_yes = {
    # Peaks save frame
    'Peak'                      : ['ID'], 
    'Peak_char'                 : ['Peak_ID', 'Spectral_dim_ID'],   # frequency
    'Peak_general_char'         : ['Peak_ID'],                      # height
    'Assigned_peak_chem_shift'  : ['Peak_ID', 'Spectral_dim_ID'],
    # Resonances save frame
    'Resonance'                 : ['ID'],
#    'Resonance_assignment'     : ['???'],
    'Spin_system'               : ['ID'],
    'Spin_system_link'          : ['From_spin_system', 'To_spin_system']
        # what about GSS typing and GSS-residue?
}
loops_no = {
    'Spectral_dim': ['ID']
}

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
        if pre in loops_ys:
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
    changes, new = [], []
    base = ds[0] # yes, we're assuming that there's always at least 1
    for d in ds[1:]:
        diff_counter, data_changes, data_new = diff_data(base, d, diff_counter)
        changes.append((tag_counter, data_changes)) # if there's no changes -- no problem, still want to increment the tag counter
        new.append((tag_counter, data_new))
        tag_counter += 1
    return (diff_counter, changes, new)



def run():
    """
    create NMR-Star files from each of the JSON files
    """
    import json
    datas = []
    for ix in range(1, 7):
        path = 'a' + str(ix) + '.txt'
        with open(path, 'r') as my_file:
#            with open('b' + str(ix) + '.txt', 'w') as out:
                data = json.loads(my_file.read())
                extracted_saves = dump2star.extract_spectra('888888', data)
                data_block = staryst.Data('mydata', extracted_saves)
                datas.append(data_block)
                # out.write(starcst.dump(data_block.translate()))
    (_, changes, new) = diff_many(datas, 1, 1)
    first = datas[0]
    with open('my_final', 'w') as out:
        out.write(starcst.dump(first.to_cst())) # but wait, we're using starYst, not starCst
    for c in changes:
        print c
    for n in new:
        print n


print run()
