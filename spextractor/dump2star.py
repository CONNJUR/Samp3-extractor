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

