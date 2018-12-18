import struct, io, sys


class BinaryMesh(io.BytesIO):
    HEADER_PACK = '10sH'
    GROUP_PACK  = 'H{}s'
    DARRAY_PACK = '<I{}d'
    def __init__(self):
        super(BinaryMesh, self).__init__()

    def write_header(self):
        bytes = struct.pack(self.HEADER_PACK, 'BINARYMESH', 1)
        self.write(bytes)

    def __repr__(self):
        return self.getvalue()

    def read_mesh(self, file):
        from struct import calcsize, unpack
        bytes =  file.read(12)
        data  =  list(unpack(self.HEADER_PACK, bytes))
        size  =  unpack('H', file.read(calcsize('H')))[0]
        data += [size]
        name  = file.read(size)
        name  = unpack('{}s'.format(size), name)
        data += list(name)
        bytes = file.read(calcsize('I'))
        size  = unpack('I', bytes)[0]
        data += [size]
        bytes = file.read(size*len('xyz')*calcsize('d'))
        vtx   = unpack('<{}d'.format(size*len('xyz')), bytes)
        data += vtx
        bytes = file.read(calcsize('I'))
        size  = unpack('I', bytes)[0]
        data += [size]
        bytes = file.read(size*len('xyz')*calcsize('d'))
        nrms  = unpack('<{}d'.format(size*len('xyz')), bytes )
        data += nrms

        return data


    def write_mesh(self, group, vertices, normals, uvs, 
        prim_indices, convert_to_binary=True):
        '''Write geometry attributes to binary buffer. '''

        self.write_header()
        self.write(self.pack_group_info(group))

        for array in (vertices, normals):
            if convert_to_binary:
                array = self.pack_double_array(array)
            self.write(array)

        if convert_to_binary:
            array = self.pack_double_array(uvs, coord=2)
            self.write(array)

        self.write(self.pack_material_slots(('default',)))
        self.write(self.pack_faces(prim_indices))

    def pack_group_info(self, group):
        fmt = self.GROUP_PACK.format(len(group))
        bytes = struct.pack(fmt, len(group), group)
        return bytes
        
    def pack_double_array(self, array, coord=3):
        '''Pack array of doubles into binary string.'''
        assert(len(array)%coord == 0)
        fmt    = self.DARRAY_PACK.format(len(array))
        bytes  = struct.pack(fmt, len(array)/coord, *array)
        return bytes

    def pack_material_slots(self, slots):
        '''Pack material slots info #slots, #name'''
        bytes = struct.pack('H', len(slots))
        for slot in slots:
            fmt   = 'H{length}s'.format(length=len(slot))
            bytes += struct.pack(fmt, len(slot), slot)
        return bytes

    def pack_faces(self, prims):
        bytes = struct.pack('I', len(prims))
        for prim in prims:
            fmt = 'H{verts}IH'.format(verts=3*prim[0])
            bytes += struct.pack(fmt, *prim)
        return bytes






def main():

    vertices = (-1, 1,-1, 1,0,-1, -1,0,1, 1,0,1)
    normals  = [0,1,0]*6
    uvs      = (0,0, 1,0, 1,1, 0,0)
    faces    = ((3,  0,0,0, 1,1,1, 2,2,2, 0), (3,  0,0,0, 3,3,3, 2,2,2, 0))
    group    = 'grid'

    # assert(isinstance(group, str))
    # assert(len(normals)%3  == 0) 
    # assert(len(vertices)%3 == 0)
    # assert(len(uvs)%2      == 0)
    # assert(len(uvs)/2      == len(normals)/3)

    if len(sys.argv) < 2:
        return 

    with open(sys.argv[-1], 'wb') as fileio:
        binary = BinaryMesh()
        binary.write_mesh(group, vertices, normals, uvs, faces)
        fileio.write(str(binary))

    with open(sys.argv[-1], 'rb') as fileio:
        binary = BinaryMesh()
        print binary.read_mesh(fileio)




        
if __name__=="__main__": main()