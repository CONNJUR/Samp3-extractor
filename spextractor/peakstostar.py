from . import starcst
from . import starast
from . import dump2star


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
    keys = ['ID'                , 'Tag_ID', 'Entry_ID', 'Annotation_list_ID',
            'Link_Sf_framecode' , 'Link_tag_category',
            'Link_key_code_1'   , 'Link_key_code_2', 
            'Link_value_1'      , 'Link_value_2', 
            'Link_tag_code'     , 'Previous_value']
    rows = []
    for (ix, (tag_id, d)) in enumerate(diffs, start=1):
        dat = d['datum']
        fie = d['field']
        typ = d['type']
        # changes
        #     Sf_framecode, tag_category, PK1, PK2, changed column
        #   peak (new)
        #     nhsqc_peaklist  Peak  ID  .  . 
        #   peak type
        #   peak freq
        #   peak height
        #   peak assignment
        #  
        new_row = [str(ix), str(tag_id), entry_id, '1']
        if [fie, typ] == ['peak', 'new']:
            new_row.extend([d['specname'] + '_peaklist', 'Peak', 
                              'ID'       , '.',
                              str(d['peakid']), '.',
                              '.'        , '.'])
        elif [fie, typ] == ['note', 'change']:
            prev = 'signal' if d['old'] == '' else d['old']
            new_row.extend([d['specname'] + '_peaklist', 'Peak',
                              'ID', '.',
                              str(d['peakid']), '.',
                              'Type', prev])
        elif [fie, typ] == ['spectrum', 'new']:
            continue # just skip it
        elif [dat, fie, typ] == ['peakdim', 'assignment', 'change']:
            prev = '.' if d['old'] is None else d['old']
            new_row.extend([d['specname'] + '_peaklist', 'Assigned_peak_chem_shift',
                            'Peak_ID', 'Spectral_dim_ID',
                            str(d['peakid']), str(d['dimid']), # off-by-one?
                            'Resonance_ID', prev])
        elif [fie, typ] == ['group', 'new']:
            new_row.extend(['my_resonances', 'Spin_system',
                            'ID', '.',
                            str(d['gid']), '.',
                            '.', '.'])
        else:
            # break
            raise ValueError('unexpected datum in diff: %s (%s)' % (d, ix))
        rows.append(new_row)
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
    """
    create an NMR-Star file from the:
     1. diffs
     2. last JSON snapshot
    """
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
    extracted = dump2star.extract_spectra(entry_id, data)
    save_diffs = extract_annotations(entry_id, tags, diffs)
    extracted[save_diffs.name] = save_diffs
    return starcst.dump(starast.Data('mydata', extracted).translate())

def run2():
    """
    create NMR-Star files from each of the JSON files
    """
    import json
    for ix in range(1, 7):
        path = 'a' + str(ix) + '.txt'
        with open(path, 'r') as my_file:
            with open('b' + str(ix) + '.txt', 'w') as out:
                data = json.loads(my_file.read())
                extracted = dump2star.extract_spectra('99999999', data)
                data_block = starast.Data('mydata', extracted)
                out.write(starcst.dump(data_block.translate()))
#print run()
run2()

