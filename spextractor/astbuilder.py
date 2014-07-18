

def build_spectra(diffs):
    spectra = []
    ix = 1
    for (spname, sp) in data['spectra'].items():
        my_sp = {
            'Spectral_peak_list.Sf_framecode': spname,
            'Spectral_peak_list.Experiment_ID': ix,
            'peaks': [],
            'peakdims': [],
            'peakheights': [],
            'dimassns': [],
            'spdims': []
        }
        spectra.append(my_sp)
        ix += 1
        


def build(annotations, diffs):
    """
      - annotations
        - notes
        - ??? note - save/loop ???
        - tags (a commit -- id, reason, entry, ??)
        - tag uses -- relationship between tags
        - tag changes -- changed things for that 'commit'
    """
    
    return None


def build_final(model):
    """
    saves:
      - 1 per spectrum
        - peaks
        - peak dims
        - peak heights
        - peak-resonance
        - spectral dims
      - 1 for resonances and GSSs
        - resonance-GSS
        - resonance-atom
        - GSS-residue
        - GSS-GSS
        - covalent links between resonances (optional)
      - 1 for shifts (optional)
    """
    