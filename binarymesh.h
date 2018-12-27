#pragma once
#include <GT/GT_GEODetail.h>
#include <GT/GT_PrimPolygonMesh.h>
#include <GT/GT_DAConstantValue.h>

#define USE_REAL_TYPE_TEMPLATE

#ifndef USE_REAL_TYPE_TEMPLATE
#define T fpreal64
#endif


namespace HDK_HAPS
{

constexpr ushort BINARYMESH_VERSION = 1;

void write_header(std::fstream &fs) {
    const char   header[]   = {'B', 'I', 'N', 'A', 'R', 'Y', 'M', 'E', 'S', 'H'};
    const ushort version    = BINARYMESH_VERSION;
    fs.write(header, 10);
    fs.write((char*)&version, 2);
}

void write_group(std::fstream & fs, const char *group) {
    const ushort lenght = strlen(group);
    fs.write((char*)&lenght, sizeof(ushort));
    fs.write(group, lenght*sizeof(char));
    
}

void write_doubles_array(std::fstream & fs, GT_DataArrayHandle & buffer, 
        const GT_DataArrayHandle & handle) {
    const uint   entries  = handle->entries();
    const size_t bytesize = entries*handle->getTupleSize()*sizeof(fpreal64);
    const fpreal64 * ptr = handle->getF64Array(buffer);
    fs.write((char*)&entries, sizeof(uint));
    fs.write((char*)ptr, bytesize);
}

template <typename T>
void write_float_array(std::fstream & fs, T * buffer, 
        const GT_DataArrayHandle & handle) {
    const uint   entries  = handle->entries();
    const size_t bytesize = entries*handle->getTupleSize()*sizeof(T);
    handle->fillArray(buffer, 0, entries, handle->getTupleSize());
    fs.write((char*)&entries, sizeof(uint));
    fs.write((char*)buffer, bytesize);   
}

void write_material_slots(std::fstream &fs, 
        const std::vector<std::string> &materials){
    
    const ushort slots = materials.size();
    fs.write((char*)&slots, sizeof(ushort));

    for(const auto & item: materials) {
        const char * matname = item.c_str();
        const ushort length = strlen(matname);
        fs.write((char*)&length, sizeof(ushort));
        fs.write((char*)matname, length*sizeof(char));   
    }
}

template<typename T>
class TesselatedDetail
{
public:
    TesselatedDetail(const GEO_Detail * gdp) {
        // I'm bothered with this copy. 
        // GT_Primitive makes copies anyway...
        gdpcopy.copy(*gdp);
        detailhandle.allocateAndSet(&gdpcopy, false);
        handle = GU_ConstDetailHandle(detailhandle);
        geometry = UTverify_cast<const GT_PrimPolygonMesh *>\
            (GT_GEODetail::makePolygonMesh(handle).get())->convex(); 
        tesselated = UTverify_cast<const GT_PrimPolygonMesh *>(geometry.get());
        const GT_PrimPolygonMesh * tmp = tesselated;
        tesselated = tesselated->createPointNormalsIfMissing();
        if (!tesselated) {
            tesselated = tmp;
        }
        if (tesselated)
            valid = true;
    }

    GT_DataArrayHandle find_attribute(const char* attr) {
        auto handle = tesselated->findAttribute(UT_StringRef(attr), vertex_owner, 0);
        if (!handle)
            handle = tesselated->findAttribute(UT_StringRef(attr), point_owner, 0);
        if (!handle)
            return nullptr;
        return handle;
    }

    void write_float_array(std::fstream &fs, const GT_DataArrayHandle & handle) {
        assert(handle != nullptr);
        const size_t new_buffer_size = handle->entries()*handle->getTupleSize();
        if (buffersize < new_buffer_size) {
            buffersize = new_buffer_size;
            buffer.reset(new T[buffersize]); 
        }
        HDK_HAPS::write_float_array<T>(fs, buffer.get(), handle);
    }

const GT_PrimPolygonMesh * mesh() const { return tesselated; }

private:
    GU_DetailHandle      detailhandle;
    GU_ConstDetailHandle handle;
    GT_PrimitiveHandle   geometry;
    GU_Detail            gdpcopy;
    const GT_PrimPolygonMesh * 
                    tesselated  = nullptr;
    std::unique_ptr<T[]> buffer = nullptr;
    GT_Owner vertex_owner = GT_OWNER_VERTEX;
    GT_Owner point_owner  = GT_OWNER_POINT;
    bool      valid       = false;
    size_t    buffersize  = 0;

};

template <typename T>
int save_binarymesh(std::fstream & fs, const GEO_Detail *detail)
{
    // Prepere for tesselation library GT_
    TesselatedDetail<T> geometry(detail);
    if (!geometry.mesh()) {
        std::cerr << "Cant create tesselated geometry. \n";
        return 0;
    }
    // header
    write_header(fs);
    // part name
    const char* group = "default";
    write_group(fs, group);
    auto positionhandle = geometry.find_attribute("P");
    auto normalhandle   = geometry.find_attribute("N");
    auto uvhandle       = geometry.find_attribute("uv");
    geometry.write_float_array(fs, positionhandle);
    geometry.write_float_array(fs, normalhandle);
    // 
    if (uvhandle) {
        // repack vector3 -> vector2
        auto uvbuffer = std::make_unique<T[]>(uvhandle->entries()*2);
        uvhandle->fillArray(uvbuffer.get(), GT_Offset(0), GT_Size(uvhandle->entries()), 2);
        uvhandle = GT_DataArrayHandle(new GT_DANumeric<T>(uvbuffer.get(), GT_Size(uvhandle->entries()), 2));
    } else {
        uvhandle = GT_DataArrayHandle(new GT_RealConstant(positionhandle->entries(), 0.0, 2)); 
    }
    geometry.write_float_array(fs, uvhandle);
    // 
    const auto tesselated = geometry.mesh();
    // Material
    ushort mindex = 0;
    std::vector<std::string> materials;
    GT_Owner prim_owner = GT_OWNER_PRIMITIVE;
    auto materialhandle = tesselated->findAttribute(
        UT_StringRef("shop_materialpath"), prim_owner, 0);

    if (materialhandle) {
        UT_StringArray shops_strings;
        materialhandle->getStrings(shops_strings);
        for(size_t m=0; m<shops_strings.entries(); ++m)
            materials.push_back(std::string(shops_strings[m]));
    } 
    //
    materials.push_back(std::string("default"));
    write_material_slots(fs, materials);
    // faces:
    const uint nfaces = tesselated->getFaceCount();
    fs.write((char*)&nfaces, sizeof(uint));
    GT_DataArrayHandle verts; GT_DataArrayHandle uniform_indexing;
    GT_DataArrayHandle vertex_indexing; GT_DataArrayHandle vert_info;
    GT_DataArrayHandle prim_info;
    //
    tesselated->getConvexArrays(verts, uniform_indexing, 
        vertex_indexing, vert_info, prim_info);
    //
    uint vidx = 0;
    GT_DataArrayHandle vperface = tesselated->getFaceCounts();
    for(size_t f=0; f<nfaces; ++f) {
        const ushort nv = vperface->getI16(GT_Offset(f));
        fs.write((char*)&nv, sizeof(ushort));
        const GT_Offset voff = tesselated->getVertexOffset(GT_Offset(f));
        for (ushort v=0; v<nv; ++v) {
            const uint pi = verts->getI32(GT_Offset(voff+v));
            //TODO: is it really the case? vertex_indexing == for f in faces for v in face...
            const uint vi = vertex_indexing->getI32(vidx);
            const uint ni = (positionhandle->entries() != normalhandle->entries()) ? vi : pi;
            const uint ti = (positionhandle->entries() != uvhandle->entries())     ? vi : pi;
            fs.write((char*)&pi, sizeof(uint)); // point index
            fs.write((char*)&ni, sizeof(uint)); // normal index
            fs.write((char*)&ti, sizeof(uint)); // uv index
            vidx++;
        }
        if (materialhandle) {
            const int materialindex = materialhandle->getStringIndex(f);
            if (materialindex < 0) {
                mindex = materials.size() - 1;
            } else {
                mindex = static_cast<ushort>(materialindex);
            }
        }
        fs.write((char*)&mindex, sizeof(ushort));
    }
    return 1;
}
} // end of namespace HDK_HAPS