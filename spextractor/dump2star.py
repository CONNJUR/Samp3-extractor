from .staryst import Loop, Save, Data


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
NULL = '.'


def extract_peaks(peaks):
    loop_peaks = Loop(['ID'], ['Type', 'Tag_row_ID'], {})
    freqs = Loop(['Peak_ID', 'Spectral_dim_ID'], ['Chem_shift_val', 'Tag_row_ID'], {})
    heights = Loop(['Peak_ID'],
                   ['Intensity_val', 'Intensity_val_err', 'Measurement_method', 'Tag_row_ID'],
                   {})
    for pk in peaks:
        pkid = str(pk['id'])
        pktype = 'signal' if pk['note'] == '' else pk['note']
        loop_peaks.add_row([pkid], [pktype, NULL])
        heights.add_row([pkid], [str(pk['height']['closest']), '0', 'height', NULL])
        for (ix, d) in enumerate(pk['position'], start=1):
            freqs.add_row([pkid, str(ix)], [str(d), NULL])
    return {
        # in order to do peakdim-resonance assignments,
        # need a dict of Sparky-resonance-names to NMRStar-resonance-names
        'Peak'              : loop_peaks,
        'Peak_char'         : freqs,
        'Peak_general_char' : heights
    }


def _trans(nucleus):
    ts = {'15N': ['15', 'N'], '13C': ['13', 'C'], '1H': ['1', 'H']}
    return ts[nucleus]


def extract_spectral_dimensions(nuclei):
    dims = Loop(['ID'], ['Atom_isotope_number', 'Atom_type'], {})
    for (ix, n) in enumerate(nuclei, start=1):
        iso, ntype = _trans(n)
        dims.add_row([str(ix)], [iso, ntype])
    return dims


def extract_spectrum(spec_id, name, sp):
    datums = {
        'Experiment_name'               : name,
        'ID'                            : str(spec_id),
        'Number_of_spectral_dimensions' : str(sp['dims']),
        'Sample_condition_list_ID'      : '?',
        'Sample_ID'                     : '?'
    }
    loops = extract_peaks(sp['peaks'])
    loops['Spectral_dim'] = extract_spectral_dimensions(sp['nuclei'])
    return Save('spectral_peak_list', 'Spectral_peak_list', datums, loops)


def extract_spectra(data):
    """
    dump object -> NMRStar spectra saveframes
    """
    saves = {}
    for (ix, (name, sp)) in enumerate(data['spectra'].items()):
        code = name + '_peaklist'
        saves[code] = extract_spectrum(str(ix + 1), name, sp)
    return saves


def generate_nmrstar(high=6):
    """
    create NMR-Star files from each of the JSON files,
    assuming systematic names for the files
    """
    from . import starcst
    import json
    for ix in range(1, high + 1):
        path = 'json_' + str(ix) + '.txt'
        with open(path, 'r') as my_file:
            with open('star_' + str(ix) + '.txt', 'w') as out:
                data = json.loads(my_file.read())
                extracted = extract_spectra(data)
                data_block = Data('99999999', extracted)
                out.write(starcst.dump(data_block.to_cst()))


if __name__ == "__main__":
    generate_nmrstar()
