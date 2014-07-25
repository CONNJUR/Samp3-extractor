


def skeleton(data):
    """
    Data/save/loop
     saves
      name
      category
      prefix
      datums
      loops
       prefix
       keys
    """
    saves = {}
    for (name, _) in data['spectra'].items():
        

def insert_diffs(star, diffs):
    for d in diffs:
        fie = d['field']
        dat = d['datum']
        typ = d['type']
        # 1. locate the place where the datum goes
        #    save/loop
        if [fie, dat, typ] == ['spectrum', 'peak', 'new']:
            
        elif [fie, dat, typ] == ['spectrum', 'peak', 'change']:
            
        # 2. figure out the PK columns of the loop
        # 3. figure out the row values
        # 4. figure out whether the row already is in the loop,
        #    based on matching the PK columns
        # 5. figure out which columns changed
        # 6. for each column which is changed, leave an entry
        #    in the diff table
        pass


keys = {
    'resonances': {
        'Resonance'         : ['ID'],
#        'Resonance_assignment': [' # not sure what to do with this.  where are resonance_sets declared?  can I assign a single resonance to a single atom?
        'Spin_system'       : ['ID'],
        'Spin_system_link'  : ['From_spin_system', 'To_spin_system']
        # what about GSS typing and GSS-residue?
    },
    'peaks': {
        'Assigned_peak_chem_shift'  : ['Peak_ID', 'Spectral_dim_ID']
        'Peak'                      : ['ID'],
        'Peak_char'                 : ['Peak_ID', 'Spectral_dim_ID'], # frequency
        'Peak_general_char'         : ['Peak_ID'],  # height
        'Spectral_dim'              : ['ID']
    }
}

def insert_diffs(model, diffs):
    for dif in diffs:
        d, f, t = dif['datum'], dif['field'], dif['type']
        spec = dif['specname'] + '_peaklist' if dif.has_key('specname') else None
        if [d,f] == ['spectrum', 'peak']:
            savename, loopname = spec, 'Peak'
        elif [d,f] == ['peak', 'note']:
            savename, loopname = spec, 'Peak'
        elif [d,f] == ['peakdim', 'assignment']:
            savename, loopname = spec, 'Assigned_peak_chem_shift'
        else:
            raise ValueError(dif)
        loop = model.saves[savename].loops[loopname]
        
