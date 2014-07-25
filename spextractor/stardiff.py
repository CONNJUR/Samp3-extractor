"""
1. compare two NMR-Star ASTs, and find the differences in the loop tables
 - new rows
 - changed rows -- although not knowing the PKs of each loop table,
   this may end up being deleted + added rows
"""

def _row_map(rows):
    """
    use columns 1 and 2 as primary key
    """
    return dict([((r[0], r[1]), r) for r in rows])


def diff_save(s1, s2):
    """
    first attempt
    """
    l = [s1.category, s1.prefix]
    r = [s2.category, s2.prefix]
    if l != r:
        raise ValueError('invalid NMR-Star comparison -- %s and %s' % (l, r))
    # ignore the rest of the datums
    for pre in set(s1.loops.keys() + s2.loops.keys()):
        if pre not in s1.loops:
            raise ValueError('illegal new loop -- %s' % pre)
        elif pre not in s2.loops:
            raise ValueError('illegal disappearing loop -- %s' % pre)
        else: # loop prefix is in both save frames
            if l1.keys != l2.keys:
                raise ValueError('incompatible loop schemas -- prefix %s, %s and %s' % (pre, l1.keys, l2.keys))
            for pk in set(l1.rows.keys() + l2.rows.keys()):
                if pk not in l1.rows:
                    # new row
                elif pk not in l2.rows:
                    raise ValueError('cannot lose row -- %s in %s, %s' % (k, l1.prefix, s1.name))
                else: # possibly changed row


def diff_loop(l1, l2, diff_counter):
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
        if pk not in l1.rows:
            l1.add_row(pk, rest)
            diff_id = diff_counter
            l1.rows[pk][-1] = str(diff_id) # TODO just assume that the last column is `Tag_row_ID`?
            diff_counter += 1
            new.append(diff_id)
            continue
        diff = l1.update_row(pk, rest)
        diff_id = diff_counter
        diff_counter += 1
        l1.rows[pk][-1] = str(diff_id) # TODO assumption ... ?
        changes.append((diff_id, diff)) # TODO don't diff the `Tag_row_ID` columns !!!
    return (diff_counter, changes, new)


def diff_save(s1, s2):
    """
    second attempt
    merge s2 into s1, modifying s1
    """
    l = [s1.category, s1.prefix]
    r = [s2.category, s2.prefix]
    if l != r:
        raise ValueError('invalid save comparison -- %s and %s' % (l, r))
    # ignore the rest of the datums
    changes = []
    for pre in set(s1.loops.keys() + s2.loops.keys()):
        if pre not in s1.loops or pre not in s2.loops:
            raise ValueError('loop name %s missing from save frame' % pre)
        loop_changes = diff_loop(s1.loops[pre], s2.loops[pre])
        changes.extend([(,) + lc for lc in loop_changes])


def diff_data(d1, d2):
    """
    merges d2 into d1, based on matching:
      1. save frame names
      2. loop names
      3. loop rows by values of key columns
    thus, d1 is modified (d2 is not) in two ways
      1. "vanilla" NMR-STAR save frames, loops, etc. are changed
      2. the new annotations save frame is *only* augmented
    """
    for name in set(d1.saves.keys() + d2.saves.keys()):
        if name not in d1.saves or name not in d2.saves:
            raise ValueError('save name %s missing from data block' % name)
        diff_save(d1.saves[name], d2.saves[name])

