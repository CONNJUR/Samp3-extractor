from . import starcst
from . import starast



def extract_peaks(entry_id, spectrum_id, peaks):
    peak_keys = ['ID', 'Entry_ID', 'Spectral_peak_list_ID', 'Type']
    height_keys = ['Peak_ID', 'Entry_ID', 'Spectral_peak_list_ID', 'Intensity_val', 'Intensity_val_err', 'Measurement_method']
    freq_keys = ['Peak_ID', 'Spectral_dim_ID', 'Entry_ID', 'Spectral_peak_list_ID', 'Chem_shift_val']
    peak_rows = []
    freq_rows = []
    height_rows = []
    for pk in peaks:
        pkid = str(pk['id'])
        pktype = 'signal' if pk['note'] == '' else pk['note']
        peak_rows.append([pkid, entry_id, spectrum_id, pktype])
        height_rows.append([pkid, entry_id, spectrum_id, str(pk['height']['closest']), '0', 'height'])
        for (ix, d) in enumerate(pk['position'], start=1):
            freq_rows.append([pkid, str(ix), entry_id, spectrum_id, str(d)])
    return [
        # in order to do peakdim-resonance assignments, need a dict of Sparky-resonance-names to NMRStar-resonance-names
        starast.Loop('Peak', peak_keys, peak_rows),
        starast.Loop('Peak_char', freq_keys, freq_rows),
        starast.Loop('Peak_general_char', height_keys, height_rows)
    ]


def _trans(nucleus):
    ts = {'15N': ['15', 'N'], '13C': ['13', 'C'], '1H': ['1', 'H']}
    return ts[nucleus]


def extract_spectral_dimensions(entry_id, spectrum_id, nuclei):
    dim_keys = ['ID', 'Entry_ID', 'Spectral_peak_list_ID', 'Atom_isotope_number', 'Atom_type']
    dim_rows = []
    for (ix, n) in enumerate(nuclei, start=1):
        iso, ntype = _trans(n)
        dim_rows.append([str(ix), entry_id, spectrum_id, iso, ntype])
    return starast.Loop('Spectral_dim', dim_keys, dim_rows)


def extract_spectrum(spec_id, entry_id, framecode, name, sp):
    datums = {
        'Entry_ID'                      : entry_id,
        'Experiment_name'               : name,
        'ID'                            : str(spec_id),
        'Number_of_spectral_dimensions' : str(sp['dims']),
        'Sample_condition_list_ID'      : '?',
        'Sample_ID'                     : '?'
    }
    loops = extract_peaks(entry_id, spec_id, sp['peaks'])
    loops.append(extract_spectral_dimensions(entry_id, spec_id, sp['nuclei']))
    return starast.Save(framecode, 'spectral_peak_list', 'Spectral_peak_list', datums, loops)


def extract_spectra(entry_id, data):
    """
    dump object -> NMRStar spectra saveframes
    """
    saves = {}
    for (ix, (name, sp)) in enumerate(data['spectra'].items()):
        code = name + '_peaklist'
        saves[code] = extract_spectrum(str(ix + 1), entry_id, code, name, sp)
    return saves


def extract_tag_annotations(entry_id, annotations):
    anno_list_id = '1' # TODO is this a constant?
    anno_keys = ['Tag_ID', 'Entry_ID', 'Annotation_list_ID', 'Annotation_code']
    anno_rows = []
    for (my_id, reasons) in annotations:
        for r in reasons:
            anno_rows.append([my_id, entry_id, anno_list_id, r])
    return starast.Loop('Tag_annotations', anno_keys, anno_rows)


def extract_tags(entry_id, tags):
    """
    String -> [(String, String)] -> Loop
    """
    anno_list_id = '1' # TODO is this a constant?
    auth = 'mwf' # TODO constant?
    tag_keys = ['ID', 'Previous_tag_ID', 'Author', 'Event_time_stamp', 'Entry_ID', 'Annotation_list_ID', 'Detail']
    tag_rows = []
    for (my_id, message) in tags:
        tag_id = str(my_id)
        prev_id = str(my_id - 1)
        tag_rows.append([tag_id, prev_id, auth, '?', entry_id, anno_list_id, message])
    return starast.Loop('Tag', tag_keys, tag_rows)


def extract_tag_diffs(entry_id, diffs):
    keys = ['ID', 'Tag_ID', 'Link_Sf_framecode', 'Link_Sf_category', 'Link_Sf_category_ID', 'Link_tag_category', 'Link_tag_code', 'Entry_ID', 'Previous_value', 'New_value']
    rows = []
    for (ix, (tag_id, d)) in enumerate(diffs, start=1):
        datum = d['datum']
        field = d['field']
        if datum == 'model':
            if field == 'spectrum':
                continue # not sure how this maps to NMR-Star
            elif field == 'group':
                pass # TODO 
            rows.append([str(ix), str(tag_id)]) # TODO 
        elif datum == 'spectrum':
            pass # TODO 
        elif datum == 'peak':
            pass # TODO 
        else:
            raise ValueError('unexpected datum in diff: %s' % datum)
        print d
        raise ValueError()
    return starast.Loop('Tag_diff', keys, rows)


def extract_annotations(entry_id, tags, diffs):
    """
    String -> [(Int, String)] -> [(???)] -> SaveFrame
    generate the annotations save frame, including the past history of each peak, resonance, gss????
    """
    datums = {
        'Entry_ID'      : entry_id          ,
        'ID'            : '1'
    }
    loops = [
        extract_tags(entry_id, tags),
        extract_tag_annotations(entry_id, []), # TODO pass in some annotations
        extract_tag_diffs(entry_id, diffs),
        # notes,
        # note_links
    ]
    return starast.Save('my_annotations', 'annotations', 'Annotation_list', datums, loops)


def run():
    import json
    entry_id = '99999999'
    tags = enumerate([
            'Sparky setup: contours, align spectra, visible planes, axis order, etc.',
            'automated NHSQC peak pick',
            'pick additional NHSQC peaks based on intensity and lineshapes',
            'identify NHSQC peaks as artifacts based on peak pattern and intensity',
            'restricted peak pick of HNCACB, CCONH-Tocsy, HNCO based on NHSQC peaks',
            'initialize GSSs based on NHSQC peaks',
        ],
        start=1)
    diffs = json.loads(open('diffs2.txt', 'r').read())
    data = json.loads(open('a6.txt', 'r').read())
    extracted = extract_spectra(entry_id, data)
    save_diffs = extract_annotations(entry_id, tags, diffs)
    extracted[save_diffs.name] = save_diffs
    return starcst.dump(starast.Data('mydata', extracted).translate())

def run2():
    import json
    for ix in range(1, 7):
        path = 'a' + str(ix) + '.txt'
        with open(path, 'r') as my_file:
            with open('b' + str(ix) + '.txt', 'w') as out:
                data = json.loads(my_file.read())
                extracted = extract_spectra('99999999', data)
                data_block = starast.Data('mydata', extracted)
                out.write(starcst.dump(data_block.translate()))
#print run()
run2()

