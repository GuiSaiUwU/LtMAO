if __name__ == '__main__':
    import os
    import sys
    curr_dir = os.path.dirname(os.path.realpath(__file__))

    # Appending src file to sys path to import as it running from there :D
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(curr_dir))))
    from LtMAO.pyRitoFile import SO

    with open(rf'{curr_dir}\files\reksai_base_burrowed_w_fin.scb', 'rb') as f:
        scb_bytes = f.read()

    with open(rf'{curr_dir}\files\reksai_base_w_knockup_timer.sco', 'r') as f:
        sco_str = f.read()

    scb = SO()
    sco = SO()
    
    scb.read_scb(raw=scb_bytes)
    sco.read_sco(raw=sco_str.encode('ascii'))
    testattr = 'signature'
    print(type(sco_str.encode('ascii')))
    #print(getattr(scb, testattr), type(getattr(scb, testattr)))
    #print(getattr(sco, testattr), type(getattr(sco, testattr)))
    
