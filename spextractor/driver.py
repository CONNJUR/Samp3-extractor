import diff
import json


def eg():
    a1 = json.loads(open('a1.txt', 'r').read())
    a2 = json.loads(open('a2.txt', 'r').read())
    return diff.semantic_diff(a1, a2)

def eg2():
    log = eg()
    ds = {'error': [], 'change': [], 'lost': [], 'new': []}
    for l in log:
        ds[l['type']].append(l)
    return ds

def eg3():
    rs = eg2()
    for t in rs.keys():
        print '\n now for %s' % t
        for r in rs[t]:
            print r


def diff_many(high_index):
    changes = []
    base_case = {'spectra': {}, 'groups': {}}
    m1 = base_case
    for ix in range(1, high_index + 1):
        path = 'a' + str(ix) + '.txt'
        with open(path, 'r') as my_file:
            m2 = json.loads(my_file.read())
            changes.append((ix, diff.semantic_diff(m1, m2)))
        m1 = m2
    return changes


def eg_many():
    diffs = []
    for (ix, cs) in diff_many(6):
        for c in cs:
            diffs.append([ix, c])
    print json.dumps(diffs)


if __name__ == "__main__":
    eg_many()

