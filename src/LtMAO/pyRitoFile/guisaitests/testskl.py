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
    #cool_github = r'https://github.com/GuiSaiUwU/EveryRiotSKLFile/raw/main/skl'
    #skl_uri = cool_github + '/assets/characters/briar/skins/base/briar_base.briar.skl'
    
    #a = get(url=skl_uri).content
    skl.read(r'C:\Users\GUILHERME AUGUSTO\Desktop\katarina.skl')
    avoid_l = []
    for joint in skl.joints:
        if 'buffbone' in joint.name.lower():
            avoid_l.append(joint.id)
    new_l = []
    for influence in skl.influences:
        if not influence in avoid_l:
            new_l.append(influence)
            
    
    skl.influences = tuple(new_l)
    print(len(skl.influences))
    skl.write(r'C:\Users\GUILHERME AUGUSTO\Desktop\katarinatest.skl')