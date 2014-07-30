from . import starast
from . import starcst


def extract_peaks(entry_id, spectrum_id, peaks):
    peak_keys = [
        'ID', 'Entry_ID', 'Spectral_peak_list_ID', 'Type', 'Tag_row_ID']
    height_keys = [
        'Peak_ID', 'Entry_ID', 'Spectral_peak_list_ID', 'Intensity_val', 
        'Intensity_val_err', 'Measurement_method', 'Tag_row_ID']
    freq_keys = [
        'Peak_ID', 'Spectral_dim_ID', 'Entry_ID', 'Spectral_peak_list_ID', 
        'Chem_shift_val', 'Tag_row_ID']
    peak_rows = []
    freq_rows = []
    height_rows = []
    NULL = '.'
    for pk in peaks:
        pkid = str(pk['id'])
        pktype = 'signal' if pk['note'] == '' else pk['note']
        peak_rows.append([pkid, entry_id, spectrum_id, pktype, NULL])
        height_rows.append([
            pkid, entry_id, spectrum_id, str(pk['height']['closest']), 
            '0', 'height', NULL])
        for (ix, d) in enumerate(pk['position'], start=1):
            freq_rows.append([pkid, str(ix), entry_id, spectrum_id, str(d), NULL])
    return [
        # in order to do peakdim-resonance assignments,
        # need a dict of Sparky-resonance-names to NMRStar-resonance-names
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


def generate_nmrstar(high=6):
    """
    create NMR-Star files from each of the JSON files,
    assuming systematic names for the files
    """
    import json
    for ix in range(1, high + 1):
        path = 'json_' + str(ix) + '.txt'
        with open(path, 'r') as my_file:
            with open('star_' + str(ix) + '.txt', 'w') as out:
                data = json.loads(my_file.read())
                extracted = extract_spectra('99999999', data)
                data_block = starast.Data('mydata', extracted)
                out.write(starcst.dump(data_block.translate()))


if __name__ == "__main__":
    generate_nmrstar()
