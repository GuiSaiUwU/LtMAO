if __name__ == '__main__':
    import os
    import sys
    curr_dir = os.path.dirname(os.path.realpath(__file__))

    # Appending src file to sys path to import as it running from there :D
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(curr_dir))))
    from LtMAO.pyRitoFile.skl import SKL

    # TODO: Delete this
    skl = SKL()

    from requests import get
    cool_github = r'https://github.com/GuiSaiUwU/EveryRiotSKLFile/raw/main/skl'
    skl_uri = cool_github + '/assets/characters/briar/skins/base/briar_base.briar.skl'
    
    a = get(url=skl_uri).content
    skl.read('', a)

    print(skl.joints[0].ibind_scale, type(skl.joints[0].ibind_scale))