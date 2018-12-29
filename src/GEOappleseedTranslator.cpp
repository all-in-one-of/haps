
#include <UT/UT_DSOVersion.h>
#include <GU/GU_Detail.h>
#include <GU/GU_PrimVolume.h>
#include <GEO/GEO_AttributeHandle.h>
#include <GEO/GEO_IOTranslator.h>
#include <SOP/SOP_Node.h>
#include <UT/UT_Assert.h>
#include <UT/UT_IOTable.h>
#include <iostream>
#include <fstream>
#include "binarymesh.h"
#include <stdio.h>


namespace HDK_HAPS 
{
class GEO_HAPSIOTranslator : public GEO_IOTranslator
{
public:
             GEO_HAPSIOTranslator() {}
    virtual ~GEO_HAPSIOTranslator() {}
    virtual GEO_IOTranslator *duplicate() const;
    virtual const char *formatName() const;
    virtual int         checkExtension(const char *name);
    virtual int         checkMagicNumber(unsigned magic);
    virtual GA_Detail::IOStatus fileLoad(GEO_Detail *gdp, UT_IStream &is, bool ate_magic);
    virtual GA_Detail::IOStatus fileSave(const GEO_Detail *gdp, std::ostream &os);
    virtual GA_Detail::IOStatus fileSaveToFile(const GEO_Detail *gdp, const char *fname);
};
}

using namespace HDK_HAPS;

GEO_IOTranslator *
GEO_HAPSIOTranslator::duplicate() const
{
    return new GEO_HAPSIOTranslator();
}
const char *
GEO_HAPSIOTranslator::formatName() const
{
    return "Appleseed binarymesh";
}
int
GEO_HAPSIOTranslator::checkExtension(const char *name) 
{
    UT_String           sname(name);
    if (sname.fileExtension() && !strcmp(sname.fileExtension(), ".binarymesh"))
        return true;
    return false;
}
int
GEO_HAPSIOTranslator::checkMagicNumber(unsigned magic)
{
    return 0;
}
GA_Detail::IOStatus
GEO_HAPSIOTranslator::fileLoad(GEO_Detail *gdp, UT_IStream &is, bool ate_magic)
{
    std::cerr << "Error: Not impemented yet.\n";
    return false;

}
GA_Detail::IOStatus
GEO_HAPSIOTranslator::fileSave(const GEO_Detail *gdp, std::ostream &os)
{
    return false;
}
GA_Detail::IOStatus
GEO_HAPSIOTranslator::fileSaveToFile(const GEO_Detail *gdp, const char *fname)
{
    if (!fname)
        return false;
    
    auto binaryfile = std::fstream(fname, 
        std::ios::out | std::ios::binary);

    bool result = false;
    if (binaryfile) {
        result = save_binarymesh(binaryfile, gdp);
        binaryfile.close();
    } 

    return result;
}

void
newGeometryIO(void *)
{
    GU_Detail::registerIOTranslator(new GEO_HAPSIOTranslator());
    UT_ExtensionList            *geoextension;
    geoextension = UTgetGeoExtensions();
    if (!geoextension->findExtension("binarymesh"))
        geoextension->addExtension("binarymesh");
}