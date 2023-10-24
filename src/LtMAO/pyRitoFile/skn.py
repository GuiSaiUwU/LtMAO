from io import BytesIO
from LtMAO.pyRitoFile.io import BinStream
from LtMAO.pyRitoFile.hash import FNV1a
from LtMAO.pyRitoFile.exceptions.sknexceptions import *
from LtMAO.pyRitoFile.structs import Vector
from typing import Optional, Tuple

def bin_hash(name):
    return f'{FNV1a(name):08x}'


class SKNVertex:
    """
    Fields:
    --------
        `Optionals`:\n
            Based in :class:`SKN` Vertex_Type.\n
            `color`: A tuple, that represents an (RGBA), vertex_type >= 1.\n
            `tangent`: :class:`Vector`, vertex_type == 2.\n

        `Persistents between every vertex type`:\n
            `position`: :class:`Vector`, local XYZ position.\n
            `normal`: :class:`Vector`, no idea.
            `influences`: A tuple, representing each unique bone id that has influence in the vertex.\n
            `weights`: A tuple, representing how much weight the certain bone id has in the vertex.\n
            # Example of reading influences and weights:\n
            # Assume influence (102, 55, 0, 0), and weights (0.65, 0.35, 0, 0).\n
            # The joint with ID of 102 have an weight of 0.65 in the vertex.\n
            # The joint with ID of 55 have an weight of 0.35 in the vertex.\n
            # Both has to be with lenght 4, since league only allows max 4 influences in a bound skin mesh.\n

    Methods:
    -------
        `__json__()`: Returns a dict of every fields. (field: value of the field)
    """
    __slots__ = (
        'position', 'influences', 'weights', 'normal', 'uv',
        'color', 'tangent'
    )

    def __init__(self):
        self.position: Vector[float, float, float] = None
        self.influences: Tuple[int, int, int, int] = None
        self.weights: Tuple[float, float, float, float] = None
        self.normal: Vector[float, float, float] = None
        self.uv: Vector[float, float] = None
        self.color: Optional[Tuple[int, int, int, int]] = None
        self.tangent: Optional[Vector[float, float, float, float]] = None

    def __json__(self):
        return {key: getattr(self, key) for key in self.__slots__}


class SKNSubmesh:
    """
    Represents a single Submesh

    Fields:
    --------
        `name`: String, name of the submesh.\n
        `bin_hash`: String, name of the submesh as FNV1a lowered hash.\n
        `vertex_start`: Integer, where the vertex start.\n
        `vertex_count`: Integer, amount of unique vertices.\n
        `index_start`: Integer, where the index starts.\n
        `index_count`: Integer, amount of unique indices.\n

    Methods:
    -------
        `__json__()`: Returns a dict of every fields. (field: value of the field)
    """
    __slots__ = (
        'name', 'bin_hash',
        'vertex_start', 'vertex_count', 'index_start', 'index_count'
    )

    def __init__(self):
        self.name: int = None
        self.bin_hash: str = None
        self.vertex_start: int = None
        self.vertex_count: int = None
        self.index_start: int = None
        self.index_count: int = None

    def __json__(self):
        return {key: getattr(self, key) for key in self.__slots__}


class SKN:
    """
    Represents a Simple Skin Mesh (3D File) from League of Legends, use .read() to get the fields initialized

    Fields:
    -------
        Optionals for version with major being 4 (4.0, 4.1, ...):\n
            `bounding_box`: A tuple of (Vector, Vector) that represents the local positions of the bounding box.\n
            `bounding_sphere`: A tuple of (Vector, float) that represents the local boundig sphere.\n
            `flags`: Integer that represents the flags.\n
            `vertex_type`: Integer that represents the vertex type.\n
            `vertex_size`: Integer that represents the vertex size.\n
        
        Persistents between every version:
            `signature`: A string that contains the hex value of the SKN signature.\n
            `version`: A float that represents the version (major.minor).\n
            `submeshes`: A list of :class:`SKNSubmesh`.\n
            `vertices`: A list of :class:`SKNVertex`.\n
            `indices`: A list of integers that represents every 3 vertice index thats connects to a triangle,
                example: (0, 5, 4, ...) vertex 0, 5, 4 connects together to make a triangle.\n
    
    Methods:
    -------
        `read()`: Used to read any supported SKN file, it fills the fields of the instance.\n
        `__json__()`: Returns a dict of every fields. (field: value of the field).\n
        `stream()`: Used to manually write / read SKN files.
    """
    __slots__ = (
        'signature', 'version', 'flags',
        'bounding_box', 'bounding_sphere', 'vertex_type', 'vertex_size',
        'submeshes', 'indices', 'vertices'
    )
    
    def __init__(self):
        self.signature: str = None
        self.version: float = None
        self.flags: Optional[int] = None
        self.bounding_box: Optional[Tuple[Vector, Vector]] = None
        self.bounding_sphere: Optional[Tuple[Vector, float]] = None
        self.vertex_type: Optional[int] = None
        self.vertex_size: Optional[int] = None
        self.submeshes: list[SKNSubmesh] = []
        self.indices: list[int] = []
        self.vertices: list[SKNVertex] = []

    def __json__(self):
        return {key: getattr(self, key) for key in self.__slots__}
    
    def stream(self, path, mode, raw=None):
        if raw != None:
            if raw == True:  # the bool True value
                return BinStream(BytesIO())
            else:
                return BinStream(BytesIO(raw))
        return BinStream(open(path, mode))

    def read(self, path: str = '', raw: Optional[bytes] = None) -> None:
        """
        Initialize the fields of :class:`SKN`

        Parameters
        ------------
        `path`: Optional[:class:`str`]
            File path to read the SKN using an existing file that should work in `open(path)`.\n
        
        `raw`: Optional[:class:`bytes`]
            None (`Default value`): Recommended if reading from an file in local memory.
            bytes: Reads SKN information from a bytes object.\n

        Raises
        --------
        `WrongSKNSignature`:
            If the SKN signature is different of 0x00112233.\n
        `UnsupportedSKNVersion`:
            If the SKN version is not in supported versions.\n
        `InvalidSKNReadUsage`:
            If raw and path is empty.\n
        """
        if not path and not raw or raw == True:
            raise InvalidSKNReadUsage(f'pyRitoFile: Provide atleast one file path or one bytes-like object as raw.')
        
        with self.stream(path, 'rb', raw) as bs:
            self.signature, = bs.read_u32()
            if self.signature != 0x00112233:
                raise WrongSKNSignature(
                    f'pyRitoFile: Failed: Read SKN {path}: Wrong signature file: {hex(self.signature)}.')
            self.signature = hex(self.signature)

            major, minor = bs.read_u16(2)
            self.version = float(f'{major}.{minor}')
            if major not in (0, 2, 4) and minor != 1:
                raise UnsupportedSKNVersion(
                    f'pyRitoFile: Failed: Read SKN {path}: Unsupported file version: {major}.{minor}.')

            if major == 0:
                # version 0 doesn't have submesh data
                index_count, vertex_count = bs.read_u32(2)

                submesh = SKNSubmesh()
                submesh.name = 'Base'
                submesh.name = bin_hash(submesh.name)
                submesh.vertex_start = 0
                submesh.vertex_count = vertex_count
                submesh.index_start = 0
                submesh.index_count = index_count
                self.submeshes.append(submesh)
            else:
                # read submeshes
                submesh_count, = bs.read_u32()
                self.submeshes = [SKNSubmesh() for i in range(submesh_count)]
                for i in range(submesh_count):
                    submesh = self.submeshes[i]
                    submesh.name, = bs.read_a_padded(64)
                    submesh.bin_hash = bin_hash(submesh.name)
                    submesh.vertex_start, submesh.vertex_count, submesh.index_start, submesh.index_count = bs.read_u32(
                        4)

                if major == 4:
                    self.flags, = bs.read_u32()

                index_count, vertex_count = bs.read_u32(2)
                # pad all this, cause we dont need
                if major == 4:
                    self.vertex_size, = bs.read_u32()
                    self.vertex_type, = bs.read_u32()
                    self.bounding_box = (bs.read_vec3()[0], bs.read_vec3()[0])
                    self.bounding_sphere = (
                        bs.read_vec3()[0], bs.read_f32()[0])

            # read unique indices
            indices = bs.read_u16(index_count)
            for i in range(0, index_count, 3):
                if indices[i] == indices[i+1] or indices[i+1] == indices[i+2] or indices[i+2] == indices[i]:
                    continue
                self.indices.extend(
                    (indices[i], indices[i+1], indices[i+2]))
            
            # read vertices
            self.vertices = [SKNVertex() for i in range(vertex_count)]
            for i in range(vertex_count):
                vertex = self.vertices[i]
                vertex.position, = bs.read_vec3()
                vertex.influences = bs.read_u8(4)
                vertex.weights = bs.read_f32(4)
                vertex.normal, = bs.read_vec3()
                vertex.uv, = bs.read_vec2()
                if self.vertex_type != None:
                    if self.vertex_type >= 1:
                        vertex.color = bs.read_u8(4)
                        if self.vertex_type == 2:
                            vertex.tangent, = bs.read_vec4()

    """def write(self, path):
        with open(path, 'wb') as f:
            bs = BinaryStream(f)

            bs.write_uint32(0x00112233)  # magic
            bs.write_uint16(1, 1)  # major, minor

            bs.write_uint32(len(self.submeshes))
            for submesh in self.submeshes:
                bs.write_padded_ascii(64, submesh.name)
                bs.write_uint32(
                    submesh.vertex_start, submesh.vertex_count, submesh.index_start, submesh.index_count)

            bs.write_uint32(len(self.indices), len(self.vertices))

            bs.write_uint16(*self.indices)

            for vertex in self.vertices:
                bs.write_vec3(vertex.position)
                bs.write_bytes(vertex.influences)
                bs.write_float(*vertex.weights)
                bs.write_vec3(vertex.normal)
                bs.write_vec2(vertex.uv)"""
