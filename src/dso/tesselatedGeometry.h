#pragma once

namespace HAPS_HDK {

// Copy attribute from GT_DataArrayHandle into a T * buffer
// and writes that float array to the stream, buffer has to be
// enough wide to store entities * tupleSize * sizeof(T)
template <typename T> 
size_t write_float_array(
        std::ostream & os, 
        T * buffer, 
        const GT_DataArrayHandle & handle) 
{
    const uint   entries  = handle->entries();
    const size_t bytesize = entries*handle->getTupleSize()*sizeof(T);
    // Does really fillArray type convert?
    handle->fillArray(buffer, 0, entries, handle->getTupleSize());
    os.write((char*)&entries, sizeof(uint));
    os.write((char*)buffer, bytesize); 
    return sizeof(uint)+bytesize;  
}

//
// Basic tesselation class using GT_ library.
// 

template<typename T>
class TesselatedGeometry
{
public:
    // We save copy of GEO_Detail and tesselate it on the fly
    TesselatedGeometry(const GEO_Detail *);
    // Find attribute by name, store attribute type in GT_Owner
    GT_DataArrayHandle find_attribute(const char *, GT_Owner attribute_owner=GT_OWNER_INVALID, 
    		const GT_Primitive * prim=nullptr) const; 
    // Save attribute to the provided stream
    size_t save_attribute(std::ostream &, const GT_DataArrayHandle &);
    // Get our copy of tesselated geometry
    const GT_PrimPolygonMesh * mesh() const { return tesselated; }
    // Are we valid? 
    bool                    isValid() const { return valid; }
    
private:
    // Tesselate routine 
    bool tesselate(const bool compute_normals=true, const bool vertex_normals=false);
    GU_DetailHandle      detailhandle;
    GU_ConstDetailHandle consthandle;
    GT_PrimitiveHandle   geometry;
    GU_Detail            gdpcopy;
    const GT_PrimPolygonMesh * 
                    tesselated  = nullptr;
    // we use to to copy attributes to stream
    std::unique_ptr<T[]> buffer = nullptr;
    // current buffer size 
    size_t    buffersize  = 0;
    bool      valid       = false;

};

} // end of namespace HAPS_HDK
