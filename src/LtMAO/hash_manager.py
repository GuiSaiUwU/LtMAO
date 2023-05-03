import requests
import os
import os.path
import json
from threading import Thread
from LtMAO import pyRitoFile

LOG = print
BIN_HASHES = (
    'hashes.binentries.txt',
    'hashes.binfields.txt',
    'hashes.bintypes.txt',
    'hashes.binhashes.txt'
)
WAD_HASHES = (
    'hashes.game.txt',
    'hashes.lcu.txt',
)
ALL_HASHES = BIN_HASHES + WAD_HASHES
HASHTABLES = {key: {} for key in ALL_HASHES}


def read_all_hashes(): CustomHashes.read_all_hashes()
def read_wad_hashes(): CustomHashes.read_wad_hashes()
def read_bin_hashes(): CustomHashes.read_bin_hashes()
def free_all_hashes(): CustomHashes.free_all_hashes()
def free_wad_hashes(): CustomHashes.free_wad_hashes()
def free_bin_hashes(): CustomHashes.free_bin_hashes()


def HASH_SEPARATOR(filename):
    # space separator in hashes txt
    # use this to skip using split()
    return 16 if filename in WAD_HASHES else 8


def to_human(size): return str(size >> ((max(size.bit_length()-1, 0)//10)*10)) + \
    ["", " KB", " MB", " GB", " TB", " PB",
        " EB"][max(size.bit_length()-1, 0)//10]


class CDTB:
    # for syncing CDTB hashes
    local_dir = './prefs/hashes/cdtb_hashes'

    def local_file(
        filename): return f'{CDTB.local_dir}/{filename}'

    def github_file(
        filename): return f'https://raw.githubusercontent.com/CommunityDragon/CDTB/master/cdragontoolbox/{filename}'
    etag_path = f'{local_dir}/etag.json'
    ETAG = {}

    @staticmethod
    def sync_hashes(*filenames):
        for filename in filenames:
            local_file = CDTB.local_file(filename)
            github_file = CDTB.github_file(filename)
            # GET request
            get = requests.get(github_file, stream=True)
            get.raise_for_status()
            # get etag and compare, new etag = sync
            etag_local = CDTB.ETAG.get(filename, None)
            etag_github = get.headers['Etag']
            if etag_local == None or etag_local != etag_github or not os.path.exists(local_file):
                # set etag
                CDTB.ETAG[filename] = etag_github
                # download file
                bytes_downloaded = 0
                chunk_size = 1024**2
                with open(local_file, 'wb') as f:
                    for chunk in get.iter_content(chunk_size):
                        bytes_downloaded += len(chunk)
                        LOG(
                            f'Downloading: {github_file}: {to_human(bytes_downloaded)}')
                        f.write(chunk)
                combine_custom_hashes(filename)
            LOG(f'Done: Sync hash: {local_file}')

    @staticmethod
    def sync_all():
        # read etags
        CDTB.ETAG = {}
        if os.path.exists(CDTB.etag_path):
            with open(CDTB.etag_path, 'r') as f:
                CDTB.ETAG = json.load(f)
        CDTB.sync_hashes(*ALL_HASHES)
        # write etags
        with open(CDTB.etag_path, 'w+') as f:
            json.dump(CDTB.ETAG, f, indent=4)


class ExtractedHashes:
    # extracted hash
    local_dir = './prefs/hashes/extracted_hashes'
    def local_file(filename): return f'{ExtractedHashes.local_dir}/{filename}'

    def extract(*file_paths):
        def bin_hash(name):
            return f'{pyRitoFile.hash.FNV1a(name):08x}'

        hashtables = {
            'hashes.binentries.txt': {},
            'hashes.binhashes.txt': {}
        }
        PRE_BIN_HASH = {
            'VfxSystemDefinitionData': bin_hash('VfxSystemDefinitionData'),
            'particlePath': bin_hash('particlePath'),
            'StaticMaterialDef': bin_hash('StaticMaterialDef'),
            'name': bin_hash('name')
        }

        def extract_skn(file_path, raw=None):
            try:
                # extract submesh hash <-> submesh name
                if raw == None:
                    skn = pyRitoFile.read_skn(file_path)
                else:
                    skn = pyRitoFile.read_skn('', raw)
                for submesh in skn.submeshes:
                    hashtables['hashes.binhashes.txt'][submesh.bin_hash] = submesh.name
                LOG(f'Done: Extract Hashes: {file_path}')
            except Exception as e:
                LOG(f'Failed: Extract Hashes: {file_path}: {e}')

        def extract_skl(file_path, raw=None):
            try:
                # extract joint hash <-> joint name
                if raw == None:
                    skl = pyRitoFile.read_skl(file_path)
                else:
                    skl = pyRitoFile.read_skl('', raw)
                for joint in skl.joints:
                    hashtables['hashes.binhashes.txt'][joint.bin_hash] = joint.name
                LOG(f'Done: Extract Hashes: {file_path}')
            except Exception as e:
                LOG(f'Failed: Extract Hashes: {file_path}: {e}')

        def extract_bin(file_path, raw=None):
            try:
                if raw == None:
                    bin = pyRitoFile.read_bin(file_path)
                else:
                    bin = pyRitoFile.read_bin('', raw)
                for entry in bin.entries:
                    # extract VfxSystemDefinitionData <-> particlePath
                    if entry.type == PRE_BIN_HASH['VfxSystemDefinitionData']:
                        particle_path_field = next((field for field in entry.data if field.hash == PRE_BIN_HASH[
                            'particlePath']), None)
                        if particle_path_field != None:
                            hashtables['hashes.binentries.txt'][entry.hash] = particle_path_field.data
                    # extract StaticMaterialDef <-> name
                    elif entry.type == PRE_BIN_HASH['StaticMaterialDef']:
                        name_field = next((field for field in entry.data if field.hash == PRE_BIN_HASH[
                            'name']), None)
                        if name_field != None:
                            hashtables['hashes.binentries.txt'][entry.hash] = name_field.data
                            LOG(f'Done: Extract Hashes: {file_path}')
            except Exception as e:
                LOG(f'Failed: Extract Hashes: {file_path}: {e}')

        def extract_wad(file_path):
            try:
                wad = pyRitoFile.read_wad(file_path)
                with wad.stream(file_path, 'rb') as bs:
                    for chunk in wad.chunks:
                        chunk.read_data(bs)
                        if chunk.extension == 'skn':
                            extract_skn(
                                f'{chunk.hash}.{chunk.extension}', chunk.data)
                        elif chunk.extension == 'skl':
                            extract_skl(
                                f'{chunk.hash}.{chunk.extension}', chunk.data)
                        elif chunk.extension == 'bin':
                            extract_bin(
                                f'{chunk.hash}.{chunk.extension}', chunk.data)
                    chunk.free_data()
                LOG(f'Done: Extract Hashes: {file_path}')
            except Exception as e:
                LOG(f'Failed: Extract Hashes: {file_path}: {e}')

        # extract hashes base on file types
        for file_path in file_paths:
            if file_path.endswith('.wad.client'):
                extract_wad(file_path)
            elif file_path.endswith('.skn'):
                extract_skn(file_path)
            elif file_path.endswith('.skl'):
                extract_skl(file_path)
            elif file_path.endswith('.bin'):
                extract_bin(file_path)
        # write out hashes txt
        for filename, hashtable in hashtables.items():
            local_file = ExtractedHashes.local_file(filename)
            sep = HASH_SEPARATOR(filename)
            # read existed extracted hashes
            if os.path.exists(local_file):
                with open(local_file, 'r') as f:
                    for line in f:
                        hashtable[line[:sep]] = line[sep+1:-1]
            # write
            with open(local_file, 'w+') as f:
                f.writelines(
                    f'{key} {value}\n'
                    for key, value in sorted(
                        hashtable.items(), key=lambda item: item[1]
                    )
                )
            LOG(f'Done: Extract: {local_file}')
            combine_custom_hashes(filename)


class CustomHashes:
    # combine with CDTB and extracted hashes
    # use for all functions in this app
    local_dir = './prefs/hashes/custom_hashes'
    def local_file(filename): return f'{CustomHashes.local_dir}/{filename}'

    @staticmethod
    def read_hashes(*filenames):
        for filename in filenames:
            local_file = CustomHashes.local_file(filename)
            # safe check
            if os.path.exists(local_file):
                # read hashes
                with open(local_file, 'r') as f:
                    sep = HASH_SEPARATOR(filename)
                    for line in f:
                        HASHTABLES[filename][line[:sep]] = line[sep+1:-1]

    @staticmethod
    def write_hashes(*filenames):
        for filename in filenames:
            local_file = CustomHashes.local_file(filename)
            # write combined hashes
            with open(local_file, 'w+') as f:
                f.writelines(
                    f'{key} {value}\n'
                    for key, value in sorted(
                        HASHTABLES[filename].items(), key=lambda item: item[1]
                    )
                )

    @staticmethod
    def read_bin_hashes():
        CustomHashes.read_hashes(*BIN_HASHES)

    @staticmethod
    def read_wad_hashes():
        CustomHashes.read_hashes(*WAD_HASHES)

    @staticmethod
    def read_all_hashes():
        CustomHashes.read_hashes(*ALL_HASHES)

    @staticmethod
    def free_hashes(*filenames):
        for filename in filenames:
            HASHTABLES[filename] = {}

    @staticmethod
    def free_bin_hashes(*filenames):
        CustomHashes.free_hashes(*BIN_HASHES)

    @staticmethod
    def free_wad_hashes(*filenames):
        CustomHashes.free_hashes(*WAD_HASHES)

    @staticmethod
    def free_all_hashes():
        CustomHashes.free_hashes(*ALL_HASHES)


def combine_custom_hashes(*filenames):
    for filename in filenames:
        hashtable = {}
        cdtb_file = CDTB.local_file(filename)
        ex_file = ExtractedHashes.local_file(filename)
        ch_file = CustomHashes.local_file(filename)
        sep = HASH_SEPARATOR(filename)
        # read cdtb hashes
        if os.path.exists(cdtb_file):
            with open(cdtb_file, 'r') as f:
                for line in f:
                    hashtable[line[:sep]] = line[sep+1:-1]
        # read extracted hashes
        if os.path.exists(ex_file):
            with open(ex_file, 'r') as f:
                for line in f:
                    hashtable[line[:sep]] = line[sep+1:-1]
        # read existed custom hashes
        if os.path.exists(ch_file):
            with open(ch_file, 'r') as f:
                for line in f:
                    hashtable[line[:sep]] = line[sep+1:-1]
        # write combined hashes
        with open(ch_file, 'w+') as f:
            f.writelines(
                f'{key} {value}\n'
                for key, value in sorted(
                    hashtable.items(), key=lambda item: item[1]
                )
            )
        LOG(f'Done: Update: {ch_file}')


def prepare(_LOG):
    # function need to call first
    def prepare_cmd():
        global LOG
        LOG = _LOG
        # ensure folder
        os.makedirs(CDTB.local_dir, exist_ok=True)
        os.makedirs(ExtractedHashes.local_dir, exist_ok=True)
        os.makedirs(CustomHashes.local_dir, exist_ok=True)
        # sync CDTB hashesh
        CDTB.sync_all()

    Thread(target=prepare_cmd, daemon=True).start()
