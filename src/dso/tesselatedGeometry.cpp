#include <GU/GU_Detail.h>
#include <GEO/GEO_ConvertParms.h>

#include <GA/GA_Range.h>

#include <GT/GT_GEODetail.h>
#include <GT/GT_RefineParms.h>
#include <GT/GT_PrimPolygonMesh.h>

#include "tesselatedGeometry.h"

#include <iostream>


namespace HAPS_HDK {

template<typename T>
TesselatedGeometry<T>::TesselatedGeometry(const GEO_Detail * gdp) 
{
    if(!gdp->isEmpty()) 
    {
       gdpcopy.copy(*gdp);
    }

    if (!gdpcopy.isEmpty() && tesselate()) 
    {
        valid = true;
    }
}

template<typename T>
bool TesselatedGeometry<T>::tesselate(const bool compute_normals, const bool vertex_normals) 
{
    // by default all to polygons.
    GEO_ConvertParms convert_parms;
    gdpcopy.convert(convert_parms);

    detailhandle.allocateAndSet(&gdpcopy, false);

    if (!detailhandle.isValid()) 
    {
        std::cerr << "!detailhandle.isValid() \n";
        return false;
    }
    
    GA_PrimitiveGroup polygroup(gdpcopy);
    GA_Iterator primit(gdpcopy.getPrimitiveRange());

    for(; !primit.atEnd(); ++primit) 
    {
        const auto prim = gdpcopy.getPrimitiveList().get(*primit);
        if (prim->getTypeId() == GA_PRIMPOLY || prim->getTypeId() == GA_PRIMMESH) 
        { 
            polygroup.add(prim);
        } 
    }

    auto poly_range = gdpcopy.getPrimitiveRange(&polygroup);

    // probably there weren't any supported prim types in detail...
    if (poly_range.isEmpty()) 
    {
        std::cerr << "poly_range.isEmpty() \n";
        return false;
    }

    auto refine_parms = GT_RefineParms();
    consthandle = GU_ConstDetailHandle(detailhandle);
    geometry    = GT_GEODetail::makePolygonMesh(consthandle, &poly_range, &refine_parms);

    if (!geometry) 
    {
        std::cerr << "GT_GEODetail::makePolygonMesh() FAILED \n";
        return false;
    }

    geometry = UTverify_cast<const GT_PrimPolygonMesh *>(geometry.get())->convex();
    assert(geometry);
    tesselated = UTverify_cast<const GT_PrimPolygonMesh *>(geometry.get());

    //TODO: should we compute vertex normals instead?
    if(compute_normals) 
    {
        // this is because ->createPointNormals*() returns nullptr if normals exist...
        const GT_PrimPolygonMesh * tmp = tesselated;
        tesselated =  UTverify_cast<const GT_PrimPolygonMesh *>(tesselated)->createPointNormalsIfMissing();
        if (!tesselated)
            tesselated = tmp;
    } 

    if(!tesselated) 
    {
        std::cerr << "createPointNormalsIfMissing() FAILED \n";
        return false; 
    }

    return true;
}

template<typename T>
GT_DataArrayHandle TesselatedGeometry<T>::find_attribute(
    const char* attribute_name, 
    GT_Owner attribute_owner,
    const GT_Primitive * prim) const
{
    if (!prim) {
        prim = tesselated;
    }
    assert(prim != nullptr);
    return prim->findAttribute(UT_StringRef(attribute_name), attribute_owner, 0);
}

template <typename T>
size_t TesselatedGeometry<T>::save_attribute(std::ostream &os, const GT_DataArrayHandle & handle) 
{
    assert(handle != nullptr);
    const size_t new_buffer_size = handle->entries()*handle->getTupleSize();
    if (buffersize < new_buffer_size) {
        buffersize = new_buffer_size;
        buffer.reset(new T[buffersize]);
        assert(buffer); 
    }
    size_t bytes = HAPS_HDK::write_float_array<T>(os, buffer.get(), handle);
    return bytes;
}

} // end of namespace HAPS_HDK

template class HAPS_HDK::TesselatedGeometry<fpreal32>;
template class HAPS_HDK::TesselatedGeometry<fpreal64>;
