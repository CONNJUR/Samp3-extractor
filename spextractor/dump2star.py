from .starast import Loop, Save, Data


loop_keys = {
    # Peaks save frame
    'Peak'                      : [['ID'], 
                                   ['Type', 'Tag_row_ID']],
    'Peak_char'                 : [['Peak_ID', 'Spectral_dim_ID'],   # frequency
                                   ['Chem_shift_val', 'Tag_row_ID']],
    'Peak_general_char'         : [['Peak_ID'],                      # height
                                   ['Intensity_val', 'Intensity_val_err', 'Measurement_method', 'Tag_row_ID']],
    'Assigned_peak_chem_shift'  : [['Peak_ID', 'Spectral_dim_ID'],
                                   ['Resonance_ID', 'Tag_row_ID']],
    # Resonances save frame
    'Resonance'                 : [['ID'],
                                   ['Name', 'Resonance_set_ID', 'Spin_system_ID', 'Tag_row_ID']],
    'Resonance_assignment'      : [['Resonance_set_ID', 'Entity_assembly_ID', 'Comp_index_ID', 'Atom_ID'],
                                   ['Tag_row_ID']],
    'Spin_system'               : [['ID'],
                                   ['Comp_index_ID', 'Entity_assembly_ID', 'Tag_row_ID']],
    'Spin_system_link'          : [['From_spin_system', 'To_spin_system'],
                                   ['Tag_row_ID']],
    # other
    'Spectral_dim'              : [['ID'],
                                   ['Atom_isotope_number', 'Atom_type']] # , 'Spectral_region']]
    # TODO what about GSS typing and GSS-residue?
}
NULL = '.'


def new_loop(name):
    pk, rest = loop_keys[name]
    return Loop(pk, rest, {})


def extract_peaks(peaks, rids):
    loop_peaks  = new_loop('Peak')
    freqs       = new_loop('Peak_char')
    heights     = new_loop('Peak_general_char')
    pkdim_assns = new_loop('Assigned_peak_chem_shift')
    for pk in peaks:
        pkid = str(pk['id'])
        pktype = 'signal' if pk['note'] == '' else pk['note']
        loop_peaks.add_row([pkid], [pktype, NULL])
        heights.add_row([pkid], [str(pk['height']['closest']), '0', 'height', NULL])
        for (ix, d) in enumerate(pk['position'], start=1):
            freqs.add_row([pkid, str(ix)], [str(d), NULL])
        for (ix, r) in enumerate(pk['resonances'], start=1):
            if r is not None:
                pkdim_assns.add_row([pkid, str(ix)], [rids[tuple(r)], NULL])
    return {
        # in order to do peakdim-resonance assignments,
        # need a dict of Sparky-resonance-names to NMRStar-resonance-names
        'Peak'                      : loop_peaks,
        'Peak_char'                 : freqs,
        'Peak_general_char'         : heights,
        'Assigned_peak_chem_shift'  : pkdim_assns
    }


def _trans(nucleus):
    ts = {'15N': ['15', 'N'], '13C': ['13', 'C'], '1H': ['1', 'H']}
    return ts[nucleus]


def extract_spectral_dimensions(nuclei):
    dims = new_loop('Spectral_dim')
    for (ix, n) in enumerate(nuclei, start=1):
        iso, ntype = _trans(n)
        dims.add_row([str(ix)], [iso, ntype])
    return dims


def extract_spectrum(spec_id, name, sp, rids):
    datums = {
        'Experiment_name'               : name,
        'ID'                            : str(spec_id),
        'Number_of_spectral_dimensions' : str(sp['dims']),
        'Sample_condition_list_ID'      : '?',
        'Sample_ID'                     : '?'
    }
    loops = extract_peaks(sp['peaks'], rids)
    loops['Spectral_dim'] = extract_spectral_dimensions(sp['nuclei'])
    return Save('spectral_peak_list', 'Spectral_peak_list', datums, loops)


def extract_spectra(spectra, rids):
    """
    dump object -> Map (GSS ID, Resonance ID) STAR-resonance-id -> NMRStar spectra saveframes
    """
    saves = {}
    for (ix, (name, sp)) in enumerate(spectra.items()):
        code = name + '_peaklist'
        saves[code] = extract_spectrum(str(ix + 1), name, sp, rids)
    return saves


def extract_assignments(groups):
    """
    res, res-ss, res-res_set :: _Resonance
    res_set-atom             :: _Resonance_assignment
    gss, gss-res             :: _Spin_system
    gss-gss                  :: _Spin_system_link
    """
    resons      = new_loop('Resonance')
    res_assn    = new_loop('Resonance_assignment')
    gss         = new_loop('Spin_system')
    gss_link    = new_loop('Spin_system_link')
    index = 1
    rids = {}
    for (gid, grp) in groups.items():
        gss.add_row([gid], [grp['residue'], '1', NULL])
        if grp['next'] != '?':
            gss_link.add_row([gid, grp['next']], [NULL])
        for (rid, res) in grp['resonances'].items():
            ix = str(index)
            # TODO what should we do for the `Resonance_set_ID`?
            #   will each resonance be in a set of size 1?
            resons.add_row([ix], [rid, ix, gid, NULL])
            if grp['residue'] != '?':
                # use NULLs to emphasize that we only care about the resonance typing here
                res_assn.add_row([ix, NULL, NULL, res['atomtype']], [NULL])
            rids[(gid, rid)] = ix
            index += 1
    datums = {}
    loops = {
        'Resonance'             : resons,
        'Resonance_assignment'  : res_assn,
        'Spin_system'           : gss,
        'Spin_system_link'      : gss_link
    }
    return (Save('resonance_linker', 'Resonance_linker_list', datums, loops), rids)


def extract(data, name='unknown'):
    save_assns, rids = extract_assignments(data['groups'])
    # then pass the rids in to use for peakdim-resonance assignments
    spectra = extract_spectra(data['spectra'], rids)
    spectra['my_resonances'] = save_assns
    return Data(name, spectra)


def generate_nmrstar(indices):
    """
    create NMR-Star files from each of the JSON files,
    assuming systematic names for the files
    """
    from . import starcst
    import json
    for ix in indices:
        path = 'json_' + str(ix) + '.txt'
        with open(path, 'r') as my_file:
            with open('star_' + str(ix) + '.txt', 'w') as out:
                json_data = json.loads(my_file.read())
                star_data = extract(json_data, '99999999')
                out.write(starcst.dump(star_data.to_cst()))


if __name__ == "__main__":
    generate_nmrstar(range(36,37))
