if __name__ == '__main__':
    import os
    import sys
    curr_dir = os.path.dirname(os.path.realpath(__file__))

    # Appending src file to sys path to import as it running from there :D
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(curr_dir))))
    from LtMAO.pyRitoFile.skn import SKN, SKNSubmesh, SKNVertex

    # TODO: Delete this

    skn = SKN()
    skn_submesh = SKNSubmesh()
    skn_vertice = SKNVertex()

    from requests import get
    skn_uri = v
    a = get(url=skn_uri).content
    skn.read('', a)
