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


annotations = [
    'Sparky setup: contours, align spectra, visible planes, axis order, etc.',
    'automated NHSQC peak pick',
    'pick additional NHSQC peaks based on intensity and lineshapes',
    'identify NHSQC peaks as artifacts based on peak pattern and intensity',
    'restricted peak pick of HNCACB, CCONH-Tocsy, HNCO based on NHSQC peaks',
    'initialize GSSs based on NHSQC peaks',
]


def diff_many(paths):
    changes = []
    base_case = {'spectra': {}, 'groups': {}}
    m1 = base_case
    for (ix, p) in enumerate(paths):
        with open(p, 'r') as my_file:
            m2 = json.loads(my_file.read())
            changes.append((ix, diff.semantic_diff(m1, m2)))
        m1 = m2
    return changes


def eg_many():
    for (ix, cs) in diff_many(['a1.txt', 'a2.txt', 'a3.txt', 'a4.txt', 'a5.txt', 'a6.txt']):
        for c in cs:
            print ix, annotations[ix], c


if __name__ == "__main__":
    eg_many()