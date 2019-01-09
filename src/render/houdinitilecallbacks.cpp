
//
// This source file is part of appleseed.
// Visit https://appleseedhq.net/ for additional information and resources.
//
// This software is released under the MIT license.
//
// Copyright (c) 2014-2018 Hans Hoogenboom, Esteban Tovagliari, The appleseedhq Organization
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.
//

// Interface header.
#include <IMG/IMG_FileTypes.h>
#include <IMG/IMG_TileDevice.h>
#include "houdinitilecallbacks.h"

// appleseed.renderer headers.
#include "renderer/kernel/aov/imagestack.h"
#include "renderer/modeling/frame/frame.h"

// appleseed.foundation headers.
#include "foundation/image/canvasproperties.h"
#include "foundation/image/image.h"
#include "foundation/image/pixel.h"
#include "foundation/platform/thread.h"
#include "foundation/utility/log.h"
#include "foundation/utility/otherwise.h"
#include "foundation/utility/string.h"

//HDK


// Standard headers.
#include <cstdio>
#include <cstring>
#include <string>
#include <iostream>
#include <algorithm>

using namespace foundation;
using namespace renderer;
using namespace std;

//
// HoudiniTileCallback.
//
// This code is based on SideFX's tomdisplay and deepmplay examples distributed with Houdini.
//
namespace HAPS {


HoudiniTileCallback* 
HoudiniTileCallback::createCallback(IMG_TileDevice* device) 
{
        return new HoudiniTileCallback(device);
}

template <typename T>
inline void 
flip_tile(const T* source, const size_t wt, const size_t ht, 
    const size_t ch, T* destination)
{
    for (size_t ty = 0; ty < ht; ++ty) {   
            const size_t destin_index = ch*wt*ty;
            const size_t source_index = ch*(wt*(ht - ty - 1));
            std::memcpy(&destination[destin_index], 
                &source[source_index], wt*ch*sizeof(T));        
    }
}

void 
HoudiniTileCallback::send_tile(const renderer::Frame* frame, 
    const size_t width, const size_t height, const size_t tile_x, const size_t tile_y) 
{
    const auto   tile  = frame->image().tile(tile_x, tile_y);
    // const size_t wtile = tile.get_width();
    // const size_t htile = tile.get_height();
    const size_t iwtile = frame->image().properties().m_tile_width;
    const size_t ihtile = frame->image().properties().m_tile_height;

    const size_t x0 = tile_x*iwtile;
    const size_t y0 = tile_y*ihtile;
    const size_t x1 = std::min(x0+iwtile, width) - 1;
    const size_t y1 = std::min(y0+ihtile, height) - 1;

    if (!m_device->writeTile(tile.get_storage(), x0, x1, y0, y1)){
        std::cerr << "Can't write tile " << tile_x << ", " << tile_y << '\n';
        std::cerr << std::flush;
        return;
    }
}

void 
HoudiniTileCallback::send_tile_flipped(const renderer::Frame* frame, 
    const size_t width, const size_t height, const size_t tile_x, const size_t tile_y) 
{
    const CanvasProperties& frame_props = frame->image().properties();
    const auto   tile  = frame->image().tile(tile_x, tile_y);
    const size_t chann = frame_props.m_channel_count;
    // const size_t wtile = tile.get_width();
    // const size_t htile = tile.get_height();
    const size_t iwtile = frame_props.m_tile_width;
    const size_t ihtile = frame_props.m_tile_height;

    // tile bounds
    const size_t x0 = tile_x*iwtile;
    const size_t y0 = height - (tile_y+1) *ihtile;
    const size_t x1 = std::min(x0+iwtile, width) - 1;
    const size_t y1 = std::min(y0+ihtile, height) - 1;

    // flip TODO switch pixel types 
    const float *  tile_ptr = reinterpret_cast<float*>(tile.get_storage());
    flip_tile<float>(tile_ptr, iwtile, ihtile, chann, m_buffer.get());

    // write to device
    if (!m_device->writeTile(m_buffer.get(), x0, x1, y0, y1)){
        std::cout << "Can't write tile " << tile_x << ", " << tile_y << '\n';
        std::cout << std::flush;
    }
}

void 
HoudiniTileCallback::on_tiled_frame_begin(const renderer::Frame* frame)
{
    const CanvasProperties& frame_props = frame->image().properties();
    const size_t wtile = frame_props.m_tile_width;
    const size_t htile = frame_props.m_tile_height;
    const size_t chann = frame_props.m_channel_count;
    const size_t size  = wtile*htile*chann;

    if (m_buffer_size < size ) {
        m_buffer.reset(new float[size]);
        m_buffer_size = size;
    }

}
void 
HoudiniTileCallback::on_tile_end(const renderer::Frame* frame, 
    const size_t tile_x, const size_t tile_y) 
{
    std::lock_guard<std::mutex> guard(m_mutex);
    const size_t width = frame->image().properties().m_canvas_width;
    const size_t height= frame->image().properties().m_canvas_height;
    send_tile_flipped(frame, width, height, tile_x, tile_y);
}

void 
HoudiniTileCallback::on_progressive_frame_update(const Frame* frame)
{
    std::lock_guard<std::mutex> guard(m_mutex);
    const CanvasProperties& frame_props = frame->image().properties();
    const size_t width = frame_props.m_canvas_width;
    const size_t height= frame_props.m_canvas_height;
    const size_t wtile = frame_props.m_tile_width;
    const size_t htile = frame_props.m_tile_height;
    const size_t chann = frame_props.m_channel_count;
    const size_t size  = wtile*htile*chann;

    if (m_buffer_size < size ) {
        m_buffer.reset(new float[size]);
        m_buffer_size = size;
    }

    for (size_t ty =0; ty <  frame_props.m_tile_count_y; ++ty)
        for (size_t tx = 0; tx < frame_props.m_tile_count_x; ++tx)
            send_tile_flipped(frame, width, height, tx, ty);
}

MPlayTileCallbackFactory::MPlayTileCallbackFactory(IMG_TileDevice* device)
        : m_callback(
            HoudiniTileCallback::createCallback(device)) {}

void MPlayTileCallbackFactory::release()
{
    delete this;
}

ITileCallback* MPlayTileCallbackFactory::create()
{
    return m_callback.get();
}

} // end of namespace HAPS






