#pragma once

#include <GT/GT_PrimPolygonMesh.h>
#include <GT/GT_DAConstantValue.h>

#include "tesselatedGeometry.h"

#include <cassert>

#ifdef LZ4
#include "lz4.h"
#endif
#if defined BINARYMESH_VERSION_4 && defined LZ4
#define FLOAT_PRECISION fpreal32
#define BINARYMESH_VERSION 4
#define USE_LZ4
#elif defined BINARYMESH_VERSION_3 && defined LZ4 
#define FLOAT_PRECISION fpreal64
#define BINARYMESH_VERSION 3
#define USE_LZ4
#else
#define FLOAT_PRECISION fpreal64
#define BINARYMESH_VERSION 1
#endif

namespace HAPS_HDK
{

// Write a binarymesh header to the stream
void write_header(std::ostream &os) 
{
    const char   header[]   = {'B', 'I', 'N', 'A', 'R', 'Y', 'M', 'E', 'S', 'H'};
    const ushort version    = BINARYMESH_VERSION;
    os.write(header, 10);
    os.write((char*)&version, 2);
}

// Write a part name into the stream
size_t write_part_name(std::ostream & os, const char *group) 
{
    const ushort length = strlen(group);
    os.write((char*)&length, sizeof(ushort));
    os.write(group, length*sizeof(char));
    return sizeof(ushort)+length*sizeof(char);
}


// Writes materials to the stream
size_t write_material_slots(
        std::ostream & os, 
        const std::vector<std::string> & materials)
{
    const ushort slots = materials.size();
    os.write((char*)&slots, sizeof(ushort));
    size_t bytes = sizeof(ushort);

    for(const auto & material: materials) 
    {
        const char * material_name = material.c_str();
        const ushort length = strlen(material_name);
        os.write((char*)&length, sizeof(ushort));
        os.write((char*)material_name, length*sizeof(char)); 
        bytes +=  sizeof(ushort) + length*sizeof(char);
    }
    return bytes;
}


int save_binarymesh(std::ostream & os, const GEO_Detail *detail)
{
    // This is our tesselated object. Only polygons.
    // It has also normals added, if they were missing.
    HAPS_HDK::TesselatedGeometry<FLOAT_PRECISION> geometry(detail);

    if (!geometry.isValid()) {
        std::cerr << "Can't create tesselated geometry. \n";
        return 0;
    }

    // header
    write_header(os);
    // datablock buffer 
    std::stringstream datablock;
    // part name
    const char* part_name = "default";
    write_part_name(datablock, part_name);

    // P,N,uv
    auto positionhandle = geometry.find_attribute("P");
    geometry.save_attribute(datablock, positionhandle);

    auto normalhandle   = geometry.find_attribute("N");
    geometry.save_attribute(datablock, normalhandle);
    
    auto uvhandle       = geometry.find_attribute("uv");
    // repack vector3 -> vector2 or make 0,0 uvs 
    if (uvhandle) {
        auto uvbuffer = std::make_unique<FLOAT_PRECISION[]>(uvhandle->entries()*2);
        uvhandle->fillArray(uvbuffer.get(), GT_Offset(0), GT_Size(uvhandle->entries()), 2);
        uvhandle = GT_DataArrayHandle(new GT_DANumeric<FLOAT_PRECISION>(uvbuffer.get(), 
            GT_Size(uvhandle->entries()), 2));
    } else {
        // TODO: make it single element -> requires different indexing
        uvhandle = GT_DataArrayHandle(new GT_RealConstant(positionhandle->entries(), 0.0, 2)); 
    }

    geometry.save_attribute(datablock, uvhandle);

    // Materials
    std::vector<std::string> materials;
    auto materialhandle = geometry.find_attribute("shop_materialpath");

    if (materialhandle) {
        UT_StringArray shops_strings;
        materialhandle->getStrings(shops_strings);
        for(const auto & shop: shops_strings) {
            materials.push_back(std::string(shop));
        }
    } 
    materials.push_back(std::string("default"));
    write_material_slots(datablock, materials);

    // faces:
    GT_DataArrayHandle point_indexing; GT_DataArrayHandle uniform_indexing;
    GT_DataArrayHandle vertex_indexing; GT_DataArrayHandle vert_info;
    GT_DataArrayHandle prim_info;

    const GT_AttributeListHandle & vertex_attribs = geometry.mesh()->getVertexAttributes();

    // TODO: we could probably remove first case
    if(geometry.mesh()->isConvexed()) {
        geometry.mesh()->getConvexArrays(point_indexing, uniform_indexing, 
            vertex_indexing, vert_info, prim_info);
    } else {
        point_indexing  =  geometry.mesh()->getVertexList();
        vertex_indexing =  vertex_attribs->get(UT_StringRef("__vertex_id"));
    }

    //
    const uint num_faces = geometry.mesh()->getFaceCount();
    datablock.write((char*)&num_faces, sizeof(uint)); 
    // if normal / uv handle differs from position we have N/uv on vertices, not points
    const bool is_normal_on_vert = positionhandle->entries() != normalhandle->entries();
    const bool is_uv_on_vert     = positionhandle->entries() != uvhandle->entries();
    //
    GT_DataArrayHandle vert_per_face = geometry.mesh()->getFaceCounts();
    for(size_t face=0, uni_vert_index=0; face<num_faces; ++face) {
        const ushort num_verts = vert_per_face->getI16(GT_Offset(face));
        datablock.write((char*)&num_verts, sizeof(ushort)); 
        const GT_Offset first_vert_offset = geometry.mesh()->getVertexOffset(GT_Offset(face));
        for (ushort vert=0; vert<num_verts; ++vert, ++uni_vert_index) {
            const uint point_index  = point_indexing->getI32(GT_Offset(first_vert_offset+vert));
            const uint vertex_index = vertex_indexing->getI32(uni_vert_index);
            const uint normal_index = is_normal_on_vert ? vertex_index : point_index;
            const uint uv_index     = is_uv_on_vert     ? vertex_index : point_index;
            datablock.write((char*)&point_index, sizeof(uint));  // point index
            datablock.write((char*)&normal_index, sizeof(uint)); // normal index
            datablock.write((char*)&uv_index, sizeof(uint));     // uv index
        }

        ushort material_index = 0;
        if (materialhandle) {
            const int shop_path_index = materialhandle->getStringIndex(face);
            // no material assign == default material (which we added as last one)
            if (shop_path_index < 0) {
                material_index = static_cast<ushort>(materials.size() - 1);
            } else {
                material_index = static_cast<ushort>(shop_path_index);
            }
        }
        datablock.write((char*)&material_index, sizeof(ushort));
    }

    #ifdef USE_LZ4
        datablock.seekp(0, std::ios::end);
        size_t bytes        = datablock.tellp(); datablock.seekg(0, std::ios::beg);
        size_t lz4bytes     = LZ4_compressBound(bytes);
        auto   compressed   = std::make_unique<char[]>(lz4bytes);
        const std::string&  temporary(datablock.str()); // good chance it won't be copied.
               lz4bytes     = LZ4_compress((const char*)temporary.c_str(), (char *)compressed.get(), bytes);
        os.write((char*)&bytes,     sizeof(size_t));
        os.write((char*)&lz4bytes,  sizeof(size_t));
        os.write((char*)compressed.get(), lz4bytes);
    #else
        os << datablock.str();
    #endif
    return 1;
}
} // end of namespace HDK_HAPS