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
template <typename T>
int save_binarymesh(std::fstream & fs, const GEO_Detail *detail)
{
    // Prepere for tesselation library GT_
    GU_Detail geometry;
    geometry.copy(*detail); // do we really need to copy?
    GU_DetailHandle detailhandle;
    detailhandle.allocateAndSet(&geometry, false);
    GU_ConstDetailHandle constdetailh(detailhandle);
    auto polymeshhandle   = GT_GEODetail::makePolygonMesh(constdetailh);
    auto polymesh         = UTverify_cast<const GT_PrimPolygonMesh *>(polymeshhandle.get());
    auto convexmeshhandle = polymesh->convex();
    auto tesselated       = UTverify_cast<const GT_PrimPolygonMesh *>(convexmeshhandle.get());
   
    if (!tesselated) {
        std::cerr << "Cant create tesselated geometry. \n";
        return 0;
    }

    // header
    write_header(fs);

     // part name
    const char* group = "default";
    write_group(fs, group);

    // points
    GT_Owner point_owner = GT_OWNER_POINT;
    GT_DataArrayHandle positionhandle = tesselated->findAttribute(
        UT_StringRef("P"), point_owner, 0);

    #ifdef USE_REAL_TYPE_TEMPLATE
    auto rawbuffer = std::make_unique<T[]>
        (positionhandle->entries()*positionhandle->getTupleSize());
    write_float_array<T>(fs, rawbuffer.get(), positionhandle);
    #else
    GT_DataArrayHandle buffer;
    write_doubles_array(fs, buffer, positionhandle);
    #endif

    // normals
    const GT_PrimPolygonMesh * tmp = tesselated;
    tesselated = tesselated->createPointNormalsIfMissing();
    if (!tesselated) {
        tesselated = tmp;
    }
    GT_Owner vertex_owner = GT_OWNER_VERTEX;
    auto normalhandle = tesselated->findAttribute(UT_StringRef("N"), vertex_owner, 0);
    if (!normalhandle) {
        normalhandle = tesselated->findAttribute(UT_StringRef("N"), point_owner, 0);
    }

    #ifdef USE_REAL_TYPE_TEMPLATE
    if (normalhandle->entries() > positionhandle->entries()) {
        rawbuffer.reset(new T[normalhandle->entries()*normalhandle->getTupleSize()]);
    }
    write_float_array<T>(fs, rawbuffer.get(), normalhandle);
    #else
    write_doubles_array(fs, buffer, normalhandle);
    #endif

    // uvs
    auto uvhandle = tesselated->findAttribute(UT_StringRef("uv"), vertex_owner, 0);
    if (!uvhandle) {
        uvhandle = tesselated->findAttribute(UT_StringRef("uv"), point_owner, 0); 
    }
    if (uvhandle) {
        // repack uvs (u, v, w, u, v, w, ...) => (u, v, u, v, ...)
        auto uvbuffer = std::make_unique<T[]>(uvhandle->entries()*2);
        uvhandle->fillArray(uvbuffer.get(), GT_Offset(0), GT_Size(uvhandle->entries()), 2);
        uvhandle = GT_DataArrayHandle(new GT_DANumeric<T>(uvbuffer.get(), GT_Size(uvhandle->entries()), 2));
        
    } else {
        uvhandle = GT_DataArrayHandle(new GT_RealConstant(positionhandle->entries(), 0.0, 2)); 
    } 
    #ifdef USE_REAL_TYPE_TEMPLATE
    if (uvhandle->entries() > normalhandle->entries()) {
        rawbuffer.reset(new T[uvhandle->entries()*uvhandle->getTupleSize()]);
    }
    write_float_array<T>(fs, rawbuffer.get(), uvhandle);
    #else
    write_doubles_array(fs, buffer, uvhandle);
    #endif

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

    //faces:
    const uint nfaces = tesselated->getFaceCount();
    fs.write((char*)&nfaces, sizeof(uint));
    GT_DataArrayHandle verts; GT_DataArrayHandle uniform_indexing;
    GT_DataArrayHandle vertex_indexing; GT_DataArrayHandle vert_info;
    GT_DataArrayHandle prim_info;

    tesselated->getConvexArrays(verts, uniform_indexing, 
        vertex_indexing, vert_info, prim_info);

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