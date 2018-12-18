import struct, io 


class BinaryMesh(io.BytesIO):
    HEADER_PACK = '10s H'
    def __init__(self):
        super(BinaryMesh, self).__init__()
        bytes = struct.pack(self.HEADER_PACK, 'BINARYMESH', 1)
        self.write(bytes)

    def __repr__(self):
        return self.getvalue()

    def write_geometry(self, group, vertices, normals, uvs, 
        prim_indices, convert_to_binary=True):
        '''Write geometry attributes to binary buffer. '''


        self.write(self.pack_group_info(group))

        for array in (vertices, normals):
            if convert_to_binary:
                array = self.pack_double_array(array)
            self.write(array)

        if convert_to_binary:
            array = self.pack_double_array(uvs, coord=2)
            self.write(array)

        self.write(self.pack_material_slots(('default',)))
        self.write(self.pack_primitives(prim_indices))

    def pack_group_info(self, group):
        fmt   = 'H {ln}s'.format(ln=len(group))
        bytes = struct.pack(fmt, len(group), group)
        return bytes
        
    def pack_double_array(self, array, coord=3):
        '''Pack array of doubles into binary string.'''
        assert(len(array)%coord == 0)
        fmt    = 'I{coord}d'.format(coord=len(array))
        bytes  = struct.pack(fmt, len(array)/coord, *array)
        return bytes

    def pack_material_slots(self, slots):
        '''Pack material slots info #slots, #name'''
        bytes = struct.pack('H', len(slots))
        for slot in slots:
            fmt   = 'H{length}s'.format(length=len(slot))
            bytes += struct.pack(fmt, len(slot), slot)
        return bytes

    def pack_primitives(self, prims):
        bytes = struct.pack('I', len(prims))
        for prim in prims:
            fmt = 'H{verts}IH'.format(verts=3*prim[0])
            bytes += struct.pack(fmt, *prim)
        return bytes




def main():

    vertices = (-1,0,-1, -1,0,1, 1,0,1, 1,0,-1)
    normals  = (1,1,1, 1,1,1, 1,1,1, 1,1,1, 1,1,1, 1,1,1)
    uvs      = (0,0, 0,1, 0,1, 1,1, 1,0, 1,0)
    faces    = ((3,  0,0,0, 1,1,1, 2,2,2, 0), (3,  0,0,0, 3,3,3, 2,2,2, 0))
    group    = 'grid'

    assert(isinstance(group, str))
    assert(len(normals)%3  == 0) 
    assert(len(vertices)%3 == 0)
    assert(len(uvs)%2      == 0)
    assert(len(uvs)/2      == len(normals)/3)


    with open("/Users/symek/Desktop/cbox/test.binarymesh", 'wb') as fileio:
        binary = BinaryMesh()
        binary.write_geometry(group, vertices, normals, uvs, faces)
        fileio.write(str(binary))




        
if __name__=="__main__": main()