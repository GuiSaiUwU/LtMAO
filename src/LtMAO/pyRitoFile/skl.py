from io import BytesIO
from LtMAO.pyRitoFile.io import BinStream
from LtMAO.pyRitoFile.structs import Matrix4, Vector, Quaternion
from LtMAO.pyRitoFile.hash import Elf, FNV1a
from LtMAO.pyRitoFile.excepts import WrongFileSignature, UnsupportedFileVersion, InvalidMethodUsage
from typing import Optional

def bin_hash(name):
    return f'{FNV1a(name):08x}'


class SKLJoint:
    """
    Represents one single joint.

    Fields:
    -------
        `id`: A integer that represents the id of the joint.\n
        `name`: A string that has the name of the joint.\n
        `bin_hash`: A string, name of the joint as FNV1a lowered hash.\n
        `parent`: A integer that points to the parent bone, -1 means world parent (not a child of any joint).\n
        `hash`: A integer that represents the hash from the curret joint.\n
        `radius`: A float that represent the radius of the joint.\n
        `flags`: A integer that represents the flags of the current joint.\n\n
        (GuiSai note: I dont know 3D Stuff)\n
        Lets assume that local stands for the local matrix of the joint.
        And the ibind stands for the inverse bind pose matrix.\n
        `local_translate`: :class:`Vector`.\n
        `local_rotate`: :class:`Quaternion`.\n
        `local_scale`: :class:`Vector`.\n
        `ibind_translate`: :class:`Vector`.\n
        `ibind_rotate`: :class:`Quaternion`.\n
        `ibind_scale`: :class:`Vector`.\n
    """
    __slots__ = (
        'id', 'name', 'bin_hash', 'parent', 'hash', 'radius', 'flags',
        'local_translate', 'local_rotate', 'local_scale',
        'ibind_translate', 'ibind_rotate', 'ibind_scale'
    )

    def __init__(self):
        self.id: Optional[int] = None
        self.name: Optional[str] = None
        self.bin_hash: Optional[str] = None
        self.parent: Optional[int] = None
        self.hash: Optional[int] = None
        self.radius: Optional[float] = None
        self.flags: Optional[int] = None
        self.local_translate: Optional[Vector] = None
        self.local_rotate: Optional[Quaternion] = None
        self.local_scale: Optional[Vector] = None
        self.ibind_translate = None
        self.ibind_rotate = None
        self.ibind_scale = None

    def __json__(self):
        return {key: getattr(self, key) for key in self.__slots__}


class SKL:
    """
    Represents a Skeleton from League of Legends, use .read() to get the fields initialized.

    Fields:
    -------\n
        `Unique from new SKL`:
            `flags`: Integer that represents the flags.\n
            `name`: String that represents the name.\n
            `asset`: String that represents the asset.\n

        `Persistents`:
            `signature`: A string that contains the hex value of the SKL signature.\n
            `version`: A integer that represents the version.\n
            `file_size`: A integer that represents the file size.\n
            `joints`: A list of :class:`SKLJoint`.\n
            `influences`: A tuple of integer that represents each unique bound joint id.
Note: not every joint is inside unfluences, because not every joint have skin bound, for example vfx bones.\n
    
    Methods:
    -------
        `read()`: Used to read any supported SKL file, it fills the fields of the instance.\n
        `write()`: Used to write the current instance.\n
        `stream()`: Used to manually write / read SKL files.\n
        `__json__()`: Returns a dict of every fields. (field: value of the field).\n
    """
    __slots__ = (
        'file_size', 'signature', 'version', 'flags',
        'name', 'asset', 'joints', 'influences'
    )

    def __init__(self):
        self.file_size: Optional[int] = None
        self.signature: Optional[str] = None
        self.version: Optional[int] = None
        self.flags: Optional[int] = None
        self.name: Optional[str] = None
        self.asset: Optional[str] = None
        self.joints: list[SKLJoint] = []
        self.influences: tuple[int, ...] = []  # type: ignore[assignment]

    def __json__(self):
        return {key: getattr(self, key) for key in self.__slots__}

    def stream(self, path, mode, raw=None):
        if raw != None:
            if raw == True:  # the bool True value
                return BinStream(BytesIO())
            else:
                return BinStream(BytesIO(raw))
        return BinStream(open(path, mode))

    def read(self, path, raw=None):
        with self.stream(path, 'rb', raw) as bs:
            # read signature first to check legacy or not
            bs.pad(4)
            signature, = bs.read_u32()
            bs.seek(0)

            if signature == 0x22FD4FC3:
                # new skl data
                self.file_size, self.signature, self.version, = bs.read_u32(
                    3)
                if self.version != 0:
                    raise UnsupportedFileVersion(
                        f'pyRitoFile: Failed: Read SKL {path}: Unsupported file version: {self.version}')
                self.signature = hex(self.signature)  # type: ignore[arg-type]
                # unknown
                self.flags, = bs.read_u16()
                # counts
                joint_count, = bs.read_u16()
                influence_count, = bs.read_u32()
                # offsets
                joints_offset, _, influences_offset, name_offset, asset_offset, _, = bs.read_i32(
                    6)
                # pad empty
                bs.pad(20)

                # read joints
                if joints_offset > 0 and joint_count > 0:
                    bs.seek(joints_offset)
                    self.joints = [SKLJoint() for i in range(joint_count)]
                    for i in range(joint_count):
                        joint = self.joints[i]

                        joint.flags, = bs.read_u16()
                        joint.id, joint.parent, = bs.read_i16(2)
                        bs.pad(2)  # pad
                        joint.hash, = bs.read_u32()
                        joint.radius, = bs.read_f32()
                        joint.local_translate, = bs.read_vec3()
                        joint.local_scale, = bs.read_vec3()
                        joint.local_rotate, = bs.read_quat()

                        joint.ibind_translate, = bs.read_vec3()
                        joint.ibind_scale, = bs.read_vec3()
                        joint.ibind_rotate, = bs.read_quat()
                        # name
                        joint_name_offset, = bs.read_i32()
                        return_offset = bs.tell()
                        bs.seek(return_offset-4 + joint_name_offset)
                        joint.name, = bs.read_c_until0()
                        joint.bin_hash = bin_hash(joint.name)
                        bs.seek(return_offset)

                # read influences
                if influences_offset > 0 and influence_count > 0:
                    bs.seek(influences_offset)
                    self.influences = bs.read_u16(influence_count)
                # name and asset string
                if name_offset > 0:
                    self.name, = bs.read_c_until0()
                if asset_offset > 0:
                    self.asset, = bs.read_c_until0()
            else:
                self.signature, = bs.read_a(8)
                if self.signature != 'r3d2sklt':
                    raise WrongFileSignature(
                        f'pyRitoFile: Failed: Read SKL {path}: Wrong file signature: {self.signature}')

                self.version, = bs.read_u32()
                if self.version not in (1, 2):
                    raise UnsupportedFileVersion(
                        f'pyRitoFile: Failed: Read SKL {path}: Unsupported file version: {self.version}')

                # skeleton id
                skeleton_id, = bs.read_u32()

                joint_count, = bs.read_u32()
                self.joints = [SKLJoint() for _ in range(joint_count)]
                old_matrices: list[Matrix4] = [None] * joint_count  # type: ignore[list-item]
                for i in range(joint_count):
                    joint = self.joints[i]

                    joint.name, = bs.read_a_padded(32)
                    joint.bin_hash = bin_hash(joint.name)
                    joint.id = i
                    joint.hash = Elf(joint.name)
                    joint.parent, = bs.read_i32()
                    joint.radius, = bs.read_f32()
                    floats = [0.0]*16
                    for c in range(3):
                        for r in range(4):
                            floats[r*4+c], = bs.read_f32()
                    floats[15] = 1.0
                    old_matrices[i] = Matrix4(*floats)

                # old matrix to local translation, ibind rotation
                for i in range(joint_count):
                    joint = self.joints[i]
                    local = old_matrices[i] if joint.parent == - \
                        1 else old_matrices[i] * old_matrices[joint.parent].inverse()  # type: ignore[index]
                    joint.local_translate, joint.local_rotate, joint.local_scale = local.decompose()
                    ibind = old_matrices[i].inverse()
                    joint.ibind_translate, joint.ibind_rotate, joint.ibind_scale = ibind.decompose()

                # read influences
                if self.version == 1:
                    self.influences = tuple(range(joint_count))

                if self.version == 2:
                    influence_count, = bs.read_u32()
                    self.influences = bs.read_u32(influence_count)

    def write(self, path, raw=None):
        with self.stream(path, 'wb', raw) as bs:
            # file size, magic, version
            bs.write_u32(0, 0x22FD4FC3, 0)

            joint_count = len(self.joints)
            influence_count = len(self.influences)
            bs.write_u16(0)  # flags
            bs.write_u16(joint_count)
            bs.write_u32(joint_count)

            joints_offset = 64
            joint_indices_offset = joints_offset + joint_count * 100
            influences_offset = joint_indices_offset + joint_count * 8
            joint_names_offset = influences_offset + joint_count * 2

            bs.write_i32(
                joints_offset,
                joint_indices_offset,
                influences_offset,
                0,  # name offset
                0,  # asset offset
                joint_names_offset
            )

            bs.write_u32(0xFFFFFFFF, 0xFFFFFFFF,
                         0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF)

            joint_offset = [None] * joint_count
            bs.seek(joint_names_offset)
            for i in range(joint_count):
                joint_offset[i] = bs.tell()
                bs.write_a(self.joints[i].name)
                bs.write_b(0)

            bs.seek(joints_offset)
            for i in range(joint_count):
                joint = self.joints[i]

                bs.write_u16(0, i)  # flags + id
                bs.write_i16(joint.parent)  # -1, cant be uint
                bs.write_u16(0)  # pad
                bs.write_u32(joint.hash)
                bs.write_f32(joint.radius)

                # local
                bs.write_vec3(joint.local_translate)
                bs.write_vec3(joint.local_scale)
                bs.write_quat(joint.local_rotate)

                # inversed bind
                bs.write_vec3(joint.ibind_translate)
                bs.write_vec3(joint.ibind_scale)
                bs.write_quat(joint.ibind_rotate)

                bs.write_u32(joint_offset[i] - bs.tell())

            # influences
            bs.seek(influences_offset)
            bs.write_u16(*[i for i in range(joint_count)])

            # joint indices
            bs.seek(joint_indices_offset)
            for i in range(joint_count):
                bs.write_u16(i)
                bs.write_u16(0)  # pad
                bs.write_u32(joint.hash)

            # file size
            bs.seek(0)
            bs.write_u32(bs.end())
            return bs.raw() if raw else None
