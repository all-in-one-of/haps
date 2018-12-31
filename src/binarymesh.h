#pragma once
#include <GT/GT_RefineParms.h>
#include <GT/GT_RefineCollect.h>
#include <GT/GT_DAConstantValue.h>
// Primitives we'd like to support
#include <GT/GT_GEODetail.h>
#include <GT/GT_PrimPolygonMesh.h>
#include <GT/GT_PrimNuPatch.h>
#include <GT/GT_PrimNURBSCurveMesh.h>
#include <GT/GT_GEOPrimTPSurf.h>
#include <GT/GT_PrimPatch.h>

#include <GA/GA_Range.h>
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

namespace HDK_HAPS
{

void write_header(std::ostream &fs) {
    const char   header[]   = {'B', 'I', 'N', 'A', 'R', 'Y', 'M', 'E', 'S', 'H'};
    const ushort version    = BINARYMESH_VERSION;
    fs.write(header, 10);
    fs.write((char*)&version, 2);
}

size_t write_part_name(std::ostream & fs, const char *group) {
    const ushort length = strlen(group);
    fs.write((char*)&length, sizeof(ushort));
    fs.write(group, length*sizeof(char));
    return sizeof(ushort)+length*sizeof(char);
    
}

template <typename T>
size_t write_float_array(std::ostream & fs, T * buffer, 
        const GT_DataArrayHandle & handle) {
    const uint   entries  = handle->entries();
    const size_t bytesize = entries*handle->getTupleSize()*sizeof(T);
    handle->fillArray(buffer, 0, entries, handle->getTupleSize());
    fs.write((char*)&entries, sizeof(uint));
    fs.write((char*)buffer, bytesize); 
    return sizeof(uint)+bytesize;  
}

size_t write_material_slots(std::ostream &fs, 
        const std::vector<std::string> &materials){
    const ushort slots = materials.size();
    fs.write((char*)&slots, sizeof(ushort));
    size_t bytes = sizeof(ushort);

    for(const auto & item: materials) {
        const char * matname = item.c_str();
        const ushort length = strlen(matname);
        fs.write((char*)&length, sizeof(ushort));
        fs.write((char*)matname, length*sizeof(char)); 
        bytes +=  sizeof(ushort) + length*sizeof(char);
    }
    return bytes;
}

template<typename T>
class TesselatedGeometry
{
public:
    using GT_DataArrayVector = std::vector<GT_DataArrayHandle>;
    TesselatedGeometry(const GEO_Detail * gdp) 
    {
        // I'm bothered with this copy. 
        // GT_Primitive makes copies anyway...
        // TODO: also I would like to copy only suppored prim types.
        if(!gdp->isEmpty()) {
           gdpcopy.copy(*gdp);
           // gdpcopy.convex(); // we would like to avoid it
        }
        if (!gdpcopy.isEmpty() && tesselate()) {
            valid = true;
        }
    }

    bool tesselate(const bool compute_normals=true, const bool vertex_normals=false) 
    {
        detailhandle.allocateAndSet(&gdpcopy, false);
        consthandle = GU_ConstDetailHandle(detailhandle);
        if (!consthandle.isValid()) {
            return false;
        }
        // TODO: 
        // This is where more logic should go for other types of primitives.
        // we could getPrimitiveByType... but then we'd end up with list of lists
        // for different types and treatment. This is good for now.
        GA_PrimitiveGroup polygroup(gdpcopy);
        GA_PrimitiveGroup nurbsgroup(gdpcopy);

        GA_Iterator primit(gdpcopy.getPrimitiveRange());
        for(; !primit.atEnd(); ++primit) {
            const auto prim = gdpcopy.getPrimitiveList().get(*primit);
            if (prim->getTypeId() == GA_PRIMPOLY || prim->getTypeId() == GA_PRIMMESH) { 
                polygroup.add(prim);
            } else if (prim->getTypeId() == GA_PRIMNURBSURF) {
                nurbsgroup.add(prim);
            }
        }
        auto poly_range   = gdpcopy.getPrimitiveRange(&polygroup);
        auto nurbs_range  = gdpcopy.getPrimitiveRange(&nurbsgroup);
        auto refine_parms = GT_RefineParms();
        auto nurbs_refiner= GT_RefineCollect();

        #if 1
        auto geo_from_nurbs = GT_GEODetail::makeDetail(consthandle, &nurbs_range);
        if (geo_from_nurbs) {    
            geo_from_nurbs = GT_Primitive::refinePrimitive(geo_from_nurbs, nullptr);
            geo_from_nurbs = dynamic_cast<GT_GEOPrimTPSurf *>
                (geo_from_nurbs.get())->buildSurface(&refine_parms);
            dynamic_cast<GT_PrimPatch *>
                (geo_from_nurbs.get())->refineToPolyMesh(nurbs_refiner);
            auto prims = nurbs_refiner.getPrimCollect();
            geo_from_nurbs = prims->getPrim(0);
            auto geo = UTverify_cast<const GT_PrimPolygonMesh *>(geo_from_nurbs.get());
            geo_from_nurbs = geo->convex();
            geometries.push_back(geo_from_nurbs.get());
            collection.appendPrimitive(geo_from_nurbs);
        }
        #endif

        if (poly_range.isEmpty()) {
            return false;
        }
        geometry = GT_GEODetail::makePolygonMesh(consthandle, &poly_range, &refine_parms);

        if (!geometry) {
            // probably there wasn't any supported prim types in detail...
            return false;
        }

        geometry = UTverify_cast<const GT_PrimPolygonMesh *>(geometry.get())->convex();
        assert(geometry);
        tesselated = UTverify_cast<const GT_PrimPolygonMesh *>(geometry.get());
        geometries.push_back(tesselated);
        collection.appendPrimitive(geometry);

        //TODO: should we compute vertex normals instead?
        if (compute_normals) {
            for (auto & geo: geometries) {
                const GT_Primitive * tmp = geo;
                geo = UTverify_cast<const GT_PrimPolygonMesh *>(geo)->createPointNormalsIfMissing();
                // this is because if normals exist, create*Normals() returns nullptr.
                if (!geo) {
                    geo = tmp;
                }
            }
        } 
        if (tesselated) {
            return true; 
        }
        return false;
    }

    GT_DataArrayHandle find_attribute(const char* attr, GT_Owner owner=GT_OWNER_INVALID, 
        const bool only_used_points=false, const GT_Primitive * prim=nullptr) 
    {
        if (!prim) {
            prim = tesselated;
        }
        assert(prim != nullptr);
        // make special case for P using getUsedPointList()
        return prim->findAttribute(UT_StringRef(attr), owner, 0);
    }

    GT_DataArrayVector find_attributes(const char* attr, GT_Owner owner=GT_OWNER_INVALID, 
        const bool only_used_points=false) 
    {
        GT_DataArrayVector arrays;
        for(size_t p=0; p<collection.entries(); ++p) {
            auto part = collection.getPrim(p);
            auto data = find_attribute(attr, owner, only_used_points, part.get());
            if (data)
                arrays.push_back(data);
        }
        return arrays;
    }

    size_t save_attribute(std::ostream &fs, const GT_DataArrayHandle & handle) 
    {
        assert(handle != nullptr);
        const size_t new_buffer_size = handle->entries()*handle->getTupleSize();
        if (buffersize < new_buffer_size) {
            buffersize = new_buffer_size;
            buffer.reset(new T[buffersize]);
            assert(buffer); 
        }
        size_t bytes = HDK_HAPS::write_float_array<T>(fs, buffer.get(), handle);
        return bytes;
    }

    size_t save_attributes(std::ostream &fs, const GT_DataArrayVector & handles) 
    {
        size_t bytes = 0;
        for(auto & handle: handles) { 
            bytes += save_attribute(fs, handle);
        }
        return bytes;   
    }

    const GT_PrimPolygonMesh * mesh()   const { return tesselated; }
    const GT_PrimCollect     * parts()  const { return &collection; }

    bool                    isValid() const { return valid; }

private:
    GU_DetailHandle      detailhandle;
    GU_ConstDetailHandle consthandle;
    GT_PrimitiveHandle   geometry;
    GU_Detail            gdpcopy;
    GT_PrimCollect       collection;
    std::vector<const GT_Primitive *> 
                            geometries;
    const GT_PrimPolygonMesh * 
                    tesselated  = nullptr;
    std::unique_ptr<T[]> buffer = nullptr;
    GT_Owner vertex_owner = GT_OWNER_VERTEX;
    GT_Owner point_owner  = GT_OWNER_POINT;
    bool      valid       = false;
    size_t    buffersize  = 0;

};

int save_binarymesh(std::ostream & fs, const GEO_Detail *detail)
{
    // This is our tesselated object. Only triangles.
    // It has also normals added, if they were absent.
    TesselatedGeometry<FLOAT_PRECISION> geometry(detail);
    if (!geometry.isValid()) {
        std::cerr << "Can't create tesselated geometry. \n";
        return 0;
    }

    // P,N,uv
    auto positionhandle = geometry.find_attribute("P");
    auto normalhandle   = geometry.find_attribute("N");
    auto uvhandle       = geometry.find_attribute("uv");
    // header
    write_header(fs);
    // datablock buffer 
    std::stringstream datablock;
    // part name
    const char* part_name = "default";
    write_part_name(datablock, part_name);
    //
    // auto positions = geometry.find_attributes("P");
    // geometry.save_attributes(datablock, positions);
    geometry.save_attribute(datablock, positionhandle);
    geometry.save_attribute(datablock, normalhandle);

    // repack vector3 -> vector2 or make 0,0 uv 
    if (uvhandle) {
        auto uvbuffer = std::make_unique<FLOAT_PRECISION[]>(uvhandle->entries()*2);
        uvhandle->fillArray(uvbuffer.get(), GT_Offset(0), GT_Size(uvhandle->entries()), 2);
        uvhandle = GT_DataArrayHandle(new GT_DANumeric<FLOAT_PRECISION>(uvbuffer.get(), 
            GT_Size(uvhandle->entries()), 2));
    } else {
        // TODO: make it single element -> requires different indexing then N
        uvhandle = GT_DataArrayHandle(new GT_RealConstant(positionhandle->entries(), 0.0, 2)); 
    }
    geometry.save_attribute(datablock, uvhandle);
    // 
    // Materials
    ushort mindex = 0;
    std::vector<std::string> materials;
    auto materialhandle = geometry.find_attribute("shop_materialpath");

    if (materialhandle) {
        UT_StringArray shops_strings;
        materialhandle->getStrings(shops_strings);
        for(auto & shop: shops_strings) {
            materials.push_back(std::string(shop));
        }
    } 
    materials.push_back(std::string("default"));
    write_material_slots(datablock, materials);

    // faces:
    GT_DataArrayHandle point_indexing; GT_DataArrayHandle uniform_indexing;
    GT_DataArrayHandle vertex_indexing; GT_DataArrayHandle vert_info;
    GT_DataArrayHandle prim_info;

    // get all in flat arrays in one shot
    assert(geometry.mesh()->isConvexed());
    geometry.mesh()->getConvexArrays(point_indexing, uniform_indexing, 
        vertex_indexing, vert_info, prim_info);
   
    //
    const uint nfaces = geometry.mesh()->getFaceCount();
    datablock.write((char*)&nfaces, sizeof(uint)); 
    //
    const bool normal_on_vert = positionhandle->entries() != normalhandle->entries();
    const bool uv_on_vert     = positionhandle->entries() != uvhandle->entries();
    //
    GT_DataArrayHandle vperface = geometry.mesh()->getFaceCounts();
    for(size_t face=0, vidx=0; face<nfaces; ++face) {
        const ushort nvertices = vperface->getI16(GT_Offset(face));
        datablock.write((char*)&nvertices, sizeof(ushort)); 
        const GT_Offset first_vert_offset = geometry.mesh()->getVertexOffset(GT_Offset(face));
        for (ushort vert=0; vert<nvertices; ++vert, ++vidx) {
            const uint point_index  = point_indexing->getI32(GT_Offset(first_vert_offset+vert));
            const uint vertex_index = vertex_indexing->getI32(vidx);
            const uint normal_index = normal_on_vert ? vertex_index : point_index;
            const uint uv_index     = uv_on_vert     ? vertex_index : point_index;
            datablock.write((char*)&point_index, sizeof(uint));  // point index
            datablock.write((char*)&normal_index, sizeof(uint)); // normal index
            datablock.write((char*)&uv_index, sizeof(uint));     // uv index
        }
        if (materialhandle) {
            const int materialindex = materialhandle->getStringIndex(face);
            if (materialindex < 0) {
                mindex = materials.size() - 1;
            } else {
                mindex = static_cast<ushort>(materialindex);
            }
        }
        datablock.write((char*)&mindex, sizeof(ushort));
    }
    #ifdef USE_LZ4
        datablock.seekp(0, std::ios::end);
        size_t bytes        = datablock.tellp(); datablock.seekg(0, std::ios::beg);
        size_t lz4bytes     = LZ4_compressBound(bytes);
        auto   compressed   = std::make_unique<char[]>(lz4bytes);
        const std::string&  temporary(datablock.str()); // good chance it won't be copied.
               lz4bytes     = LZ4_compress((const char*)temporary.c_str(), (char *)compressed.get(), bytes);
        fs.write((char*)&bytes,     sizeof(size_t));
        fs.write((char*)&lz4bytes,  sizeof(size_t));
        fs.write((char*)compressed.get(), lz4bytes);
    #else
        fs << datablock.str();
    #endif
    return 1;
}
} // end of namespace HDK_HAPS