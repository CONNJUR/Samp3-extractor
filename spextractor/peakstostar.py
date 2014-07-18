from .starcst import build_value, Data, Save, Loop
from . import starcst



def _pre(prefix, keys):
    return [(prefix + key) for key in keys]

def _row(*vals):
    return map(build_value, vals)


def dump_peaks(entry_id, spectrum_id, peaks):
    peak_keys = ['Entry_ID', 'ID', 'Spectral_peak_list_ID', 'Type']
    freq_keys = ['Entry_ID', 'Peak_ID', 'Spectral_dim_ID', 'Spectral_peak_list_ID', 'Chem_shift_val']
    height_keys = ['Entry_ID', 'Peak_ID', 'Spectral_peak_list_ID', 'Intensity_val', 'Intensity_val_err', 'Measurement_method']
    peak_rows = []
    freq_rows = []
    height_rows = []
    for pk in peaks:
        pkid = str(pk['id'])
        pktype = 'signal' if pk['note'] == '' else pk['note']
        peak_rows.append(_row(entry_id, pkid, spectrum_id, pktype))
        height_rows.append(_row(entry_id, pkid, spectrum_id, str(pk['height']['closest']), '0', 'height'))
        for (ix, d) in enumerate(pk['position'], start=1):
            freq_rows.append(_row(entry_id, pkid, str(ix), spectrum_id, str(d)))
    return [
        # in order to do peakdim-resonance assignments, need a dict of Sparky-resonance-names to NMRStar-resonance-names
        Loop(_pre('Peak.', peak_keys), peak_rows),
        Loop(_pre('Peak_char.', freq_keys), freq_rows),
        Loop(_pre('Peak_general_char.', height_keys), height_rows),
    ]


def _trans(nucleus):
    ts = {'15N': ['15', 'N'], '13C': ['13', 'C'], '1H': ['1', 'H']}
    return ts[nucleus]


def dump_spectral_dimensions(entry_id, spectrum_id, nuclei):
    dim_keys = ['Entry_ID', 'ID', 'Spectral_peak_list_ID', 'Atom_isotope_number', 'Atom_type']
    dim_rows = []
    for (ix, n) in enumerate(nuclei, start=1):
        iso, ntype = _trans(n)
        dim_rows.append(_row(entry_id, str(ix), spectrum_id, iso, ntype))
    return Loop(_pre('Spectral_dim.', dim_keys), dim_rows)


def dump_spectrum(spec_id, entry_id, framecode, name, sp):
    datums = {
        'Sf_category'                   : 'spectral_peak_list',
        'Sf_framecode'                  : framecode,
        'Entry_ID'                      : entry_id,
        'Experiment_name'               : name,
        'ID'                            : str(spec_id),
        'Number_of_spectral_dimensions' : str(sp['dims']),
        'Sample_condition_list_ID'      : '?',
        'Sample_ID'                     : '?'
    }
    prefix = 'Spectral_peak_list.'
    pre_datums = dict([(prefix + key, build_value(value)) for (key, value) in datums.items()])
    loops = dump_peaks(entry_id, spec_id, sp['peaks'])
    loops.append(dump_spectral_dimensions(entry_id, spec_id, sp['nuclei']))
    return Save(pre_datums, loops)


def dump(entry_id, data):
    """
    dump object -> NMRStar spectra saveframes
    """
    saves = {}
    for (ix, (name, sp)) in enumerate(data['spectra'].items()):
        code = name + '_peaklist'
        saves[name] = dump_spectrum(str(ix + 1), entry_id, code, name, sp)
    return saves


def run():
    import json
    data = json.loads(open('a6.txt', 'r').read())
    dumped = dump('99999999', data)
    return starcst.dump(Data('mydata', dumped))

print run()
