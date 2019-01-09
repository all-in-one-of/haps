
// //
// // This source file is part of appleseed.
// // Visit https://appleseedhq.net/ for additional information and resources.
// //
// // This software is released under the MIT license.
// //
// // Copyright (c) 2010-2013 Francois Beaune, Jupiter Jazz Limited
// // Copyright (c) 2014-2018 Francois Beaune, The appleseedhq Organization
// //
// // Permission is hereby granted, free of charge, to any person obtaining a copy
// // of this software and associated documentation files (the "Software"), to deal
// // in the Software without restriction, including without limitation the rights
// // to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// // copies of the Software, and to permit persons to whom the Software is
// // furnished to do so, subject to the following conditions:
// //
// // The above copyright notice and this permission notice shall be included in
// // all copies or substantial portions of the Software.
// //
// // THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// // IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// // FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// // AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// // LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// // OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// // THE SOFTWARE.
// //

// appleseed.renderer headers. Only include header files from renderer/api/.
#include "renderer/api/bsdf.h"
#include "renderer/api/camera.h"
#include "renderer/api/color.h"
#include "renderer/api/environment.h"
#include "renderer/api/environmentedf.h"
#include "renderer/api/environmentshader.h"
#include "renderer/api/frame.h"
#include "renderer/api/light.h"
#include "renderer/api/log.h"
#include "renderer/api/material.h"
#include "renderer/api/object.h"
#include "renderer/api/project.h"
#include "renderer/api/rendering.h"
#include "renderer/api/scene.h"
#include "renderer/api/surfaceshader.h"
#include "renderer/api/utility.h"

// // appleseed.foundation headers.
#include "foundation/core/appleseed.h"
#include "foundation/math/matrix.h"
#include "foundation/math/scalar.h"
#include "foundation/math/transform.h"
#include "foundation/math/vector.h"
#include "foundation/utility/containers/dictionary.h"
#include "foundation/utility/log/consolelogtarget.h"
#include "foundation/utility/autoreleaseptr.h"
#include "foundation/utility/searchpaths.h"

// HDK
#include <IMG/IMG_TileDevice.h>
#include <IMG/IMG_TileOptions.h>
#include <TIL/TIL_TileMPlay.h>

// our version of appleseed.cli file
#include "houdinitilecallbacks.h"

// Standard headers.
#include <cstddef>
#include <memory>
#include <string>
#include <iostream>
#include <fstream>
#include <string>
#include <chrono>
#include <thread>
#include <cstdio>

#include <vector>
#include <algorithm>
#include <iterator>
#include <iostream>
#include <cassert>
#include <sstream>

// Define shorter namespaces for convenience.
namespace asf = foundation;
namespace asr = renderer;

// Appleseed to Houdini pixel format mapping:
IMG_DataType HAPS_PixelFormat(asf::PixelFormat format)
{
    switch(format)
    {
        case asf::PixelFormatUInt8  : return IMG_INT8;
        case asf::PixelFormatUInt16 : return IMG_USHORT;
        case asf::PixelFormatUInt32 : return IMG_INT32;
        case asf::PixelFormatHalf   : return IMG_HALF;
        case asf::PixelFormatFloat  : return IMG_FLOAT32;
        case asf::PixelFormatDouble : return IMG_DT_UNDEFINED;
        default                     : return IMG_DT_UNDEFINED;
    }
};

enum HAPS_RenderMode {
    Default,
    Ipr,
};

IMG_ColorModel HAPS_ColorModel(const size_t channel_count)
{
    switch(channel_count)
    {
        case 3 : IMG_RGB;
        case 4 : IMG_RGBA;
        default: IMG_CM_UNDEFINED;
    }
};

class HAPSRendererController: 
    public asr::DefaultRendererController
 {
 public:
    // void on_progress() override { }
    void set_status(const asr::IRendererController::Status status )
    {
        m_status = status;
    }
    asr::IRendererController::Status get_status() const override {
        return m_status;
    }
private:
    std::atomic<asr::IRendererController::Status> m_status;
 };

 template <typename T>
bool parse_string_to_digits(const std::string &line, std::vector<T> &array, const size_t size = 16)
{
    std::istringstream iss(line);

    std::copy(std::istream_iterator<T>(iss),
        std::istream_iterator<T>(),
        std::back_inserter(array));

    if (array.size() != size)
        return false;

    return true;
}

bool copy_stdin_to_file(std::string &filename, std::string &port, int & mode)
{
    const char* fname  = std::tmpnam(nullptr);
    if (!fname)
        return false;

    auto stream = std::ofstream(
        fname, std::ios::out | std::ios::binary);

    std::string line;
    // I can remove it because custom tags on camera can hold this data better 
    // first line is: "(int)port (int)render_mode" (0=final, 1=interactive)
    #if 0
    std::getline(std::cin, line);
    if ([&]() { 
        return !line.empty() && 
        std::all_of(
            line.begin(), 
            line.end(), 
            [](const char &w) { return ::isdigit(w) || std::isspace(w); }
            );
        }() == true) 
    {
        auto port_and_mode = std::vector<int>{};
        if (parse_string_to_digits<int>(line, port_and_mode, 2))
        {
            port = std::to_string(port_and_mode[0]);
            mode = port_and_mode[1];
            assert(mode == 0 || mode == 1);
        }

    } else {
        // this is already xml, add to the stream
        stream << line;
    }
    #endif
    // I generate output in single line for interactive renders.
    std::getline(std::cin, line);
    stream << line << '\n';
    #if 0
    // while(!std::cin.eof() && !stream.bad()) {
    //     std::getline(std::cin, line);
    //     stream << line << '\n';
    //     if (line.compare(std::string("</project>")) == 0)
    //         break;
    // }
    // if (stream.bad()) {
    //     stream.close();
    //     return false;
    // }
    #endif

    stream.close();
    filename = fname;
    return true;    
}

bool
send_tile_definition(IMG_TileDevice *dev, const uint port,
    const asf::CanvasProperties & image_properties)
{
    const auto width   = image_properties.m_canvas_width;
    const auto height  = image_properties.m_canvas_height;
    const auto twidth  = image_properties.m_tile_width;
    const auto theight = image_properties.m_tile_height;
    const auto colors  = HAPS_ColorModel(image_properties.m_channel_count);
    const auto pixels  = HAPS_PixelFormat(static_cast<asf::PixelFormat>
        (image_properties.m_pixel_format));

    IMG_TileOptionList  tile_option_list;
    // deletion is handled by IMG_TileOptionList;
    auto tile_info = new IMG_TileOptions();
    const auto port_s = std::to_string(port);
    tile_info->setPlaneInfo("appleseed","beauty", 0, pixels, colors);
    tile_info->setFormatOption("socketport", port_s.c_str());
    tile_option_list.append(tile_info);
    if (!dev->openMulti(tile_option_list, width, height, twidth, theight, 1.0)) {
        return false;
    }
    return true;
}

void update_camera_xform(asr::Project* project, const std::vector<double> & xform)
{
    auto camera = project->get_uncached_active_camera();
    camera->transform_sequence().clear();
    const double* raw = reinterpret_cast<const double*>(&xform[0]);
    camera->transform_sequence().set_transform(
        0.0f,
        asf::Transformd::from_local_to_parent(
            asf::Matrix4d::from_array(raw)));

}

void update_camera(asr::Project* project, HAPSRendererController* controller) 
{
    std::string line;
    std::vector<double> xform;

    while(!std::cin.eof() && !std::cin.bad()) {

        xform.clear();
        std::getline(std::cin, line);

        if(line.empty())
            continue;
        
        if (!parse_string_to_digits<double>(line, xform))
            continue;

        controller->set_status(asr::IRendererController::PauseRendering);
        update_camera_xform(project, xform);
        controller->set_status(asr::IRendererController::RestartRendering);
        project->get_frame()->clear_main_and_aov_images();
        controller->set_status(asr::IRendererController::ContinueRendering);
    }
}



int main()
{
    std::unique_ptr<asf::ILogTarget> log_target(asf::create_console_log_target(stderr));
    asr::global_logger().add_target(log_target.get());

    // Print appleseed's version string.
    RENDERER_LOG_INFO("%s", asf::Appleseed::get_synthetic_version_string());

    auto port = std::string("0"); //tmp
    int  mode = 0;
    // workaround before implementing projectFileReader::from_stream()
    std::string filename;
    if(!copy_stdin_to_file(filename, port, mode)) {
        RENDERER_LOG_INFO("Couldn't open stream." );
        return 1;
    }

    auto projectReader = asr::ProjectFileReader();

    const char *project_name = filename.c_str();
    const char *schema_name  = nullptr; //"/Applications/Appleseed/schemas/project.xsd";
    auto options = asr::ProjectFileReader::OmitProjectSchemaValidation;
    auto project = projectReader.read(project_name, schema_name, options);

    // Check reading extra info from camera node:
    uint default_number = 0;
    auto camera_parms = project->get_uncached_active_camera()->get_parameters();
    uint socketport   = camera_parms.get_optional("socketport", default_number);
    // 1: progressive, 0: normal, -1: render to disk
    uint rendermode   = camera_parms.get_optional("preview", default_number);

    RENDERER_LOG_INFO("Rendering to Houdini on port: %d", socketport);

    // Device for RenderView in Houdini   
    const auto image_properties = project->get_frame()->image().properties();
    auto device = std::unique_ptr<IMG_TileDevice>(IMG_TileDevice::newMPlayDevice(0));
    if (!send_tile_definition(device.get(), socketport, image_properties))
    {
        return 1;
    }
    // Callback to communicate with Houdini RenderView window:
    std::unique_ptr<asr::ITileCallbackFactory> mplay_tile_callback_factory;
    mplay_tile_callback_factory.reset(new HAPS::MPlayTileCallbackFactory(device.get()));

    asr::ParamArray render_parameters;
    // mode was gathered as a second int of first line of stdin
    if (rendermode == HAPS_RenderMode::Ipr) {
        render_parameters = project->configurations()\
            .get_by_name("interactive")->get_inherited_parameters();
    } else {
        render_parameters = project->configurations()\

            .get_by_name("final")->get_inherited_parameters();  
    }

    // My controler sets status to communicate with renderer thread 
    // (in update_camera )
    HAPSRendererController renderer_controller;
    // Create the master renderer.
    std::unique_ptr<asr::MasterRenderer> renderer(
        new asr::MasterRenderer(
            project.ref(),
            render_parameters,
            &renderer_controller,
            mplay_tile_callback_factory.get()));

    // start thread which will listen to changes for ipr... dirty
    std::thread{update_camera, project.get(), &renderer_controller }.detach();
    // Render the frame.
    renderer->render();

    // Save the frame to disk.
    // project->get_frame()->write_main_image("test.png");

    // // Save the project to disk.
    // asr::ProjectFileWriter::write(project.ref(), "output/test.appleseed");

    // Make sure to delete the master renderer before the project and the logger / log target.
    renderer.reset();
    RENDERER_LOG_INFO("Removing tmp file %s", project_name);
    std::remove(project_name);

    return 0;
}
