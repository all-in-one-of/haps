//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Esteban Tovagliari. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////


#include "foundation/image/image.h"
#include "foundation/utility/autoreleaseptr.h"
#include "renderer/api/aov.h"
#include "renderer/api/frame.h"
#include "renderer/api/log.h"
#include "renderer/api/rendering.h"
#include "renderer/api/utility.h"
#include "renderer/api/version.h"

// HDK
#include <IMG/IMG_TileDevice.h>
#include <IMG/IMG_TileOptions.h>
#include <TIL/TIL_TileMPlay.h>

#include <vector>

namespace asf = foundation;
namespace asr = renderer;

namespace HAPS
{


class DisplayTileCallback: public ProgressTileCallback
{
public:

    explicit DisplayTileCallback( const asr::ParamArray &params ) : 
        ProgressTileCallback(), 
        m_displays_initialized( false )
    {
        // Create display layers.
        m_layers.reserve( params.dictionaries().size() );
        for( auto it( params.dictionaries().begin() ), eIt( params.dictionaries().end() ); it != eIt; ++it )
        {
            m_layers.push_back( new DisplayLayer( it.key(), it.value() ) );
        }
    }

    ~DisplayTileCallback() override
    {
        for( DisplayLayer *layer : m_layers )
        {
            delete layer;
        }
    }

    void release() override
    {
        // We don't need to do anything here.
        // The tile callback factory deletes this instance.
    }

    void on_tile_begin(const asr::Frame *frame, const size_t tileX, const size_t tileY) override
    {
        const asf::CanvasProperties &props = frame->image().properties();
        const size_t x = tileX * props.m_tile_width;
        const size_t y = tileY * props.m_tile_height;

        boost::lock_guard<boost::mutex> guard( m_mutex );

        if( m_displays_initialized )
        {
            for( DisplayLayer *layer : m_layers )
            {
                layer->hightlight_region( x, y, props.m_tile_width, props.m_tile_height );
            }
        }
    }

    void on_tile_end(const asr::Frame *frame, const size_t tileX, const size_t tileY) override
    {
        boost::lock_guard<boost::mutex> guard( m_mutex );

        init_layer_displays( frame );

        for( DisplayLayer *layer : m_layers )
        {
            layer->write_tile( tileX, tileY );
        }

        log_progress( frame, tileX, tileY );
    }

    void on_progressive_frame_update( const asr::Frame* frame ) override
    {
        boost::lock_guard<boost::mutex> guard( m_mutex );

        init_layer_displays( frame );

        const asf::CanvasProperties &frame_props = frame->image().properties();

        for( size_t ty = 0; ty < frame_props.m_tile_count_y; ++ty )
        {
            for( size_t tx = 0; tx < frame_props.m_tile_count_x; ++tx )
            {
                for( DisplayLayer *layer : m_layers )
                {
                    layer->write_tile( tx, ty );
                }
            }
        }
    }

private :

    void init_layer_displays( const asr::Frame* frame )
    {
        if( !m_displays_initialized )
        {
            const asf::CanvasProperties &frameProps = frame->image().properties();

            Box2i displayWindow( V2i( 0, 0 ), V2i( frameProps.m_canvas_width - 1, frameProps.m_canvas_height - 1 ) );

            const asf::AABB2u &cropWindow = frame->get_crop_window();
            Box2i dataWindow = Box2i( V2i( cropWindow.min[0], cropWindow.min[1] ), V2i( cropWindow.max[0], cropWindow.max[1] ) );

            for( DisplayLayer *layer : m_layers )
            {
                layer->init_display( frame, displayWindow, dataWindow );
            }

            m_displays_initialized = true;
        }
    }

    std::vector<DisplayLayer*> m_layers;
    bool m_displays_initialized;
};

class DisplayTileCallbackFactory: public asr::ITileCallbackFactory
{
public:

    explicit DisplayTileCallbackFactory( const asr::ParamArray &params )
    {
        device.resert(IMG_TileDevice::newMPlayDevice(0));
        m_callback = new DisplayTileCallback(params, device.get());
    }

    ~DisplayTileCallbackFactory() override
    {
        delete m_callback;
    }

    // Delete this instance.
    void release() override
    {
        delete this;
    }

    // Return a new tile callback instance.
    asr::ITileCallback *create() override
    {
        return m_callback;
    }

private:
    DisplayTileCallback *m_callback;
    std::unique_ptr<IMG_TileDevice> device;

};

} // end of HAPS namespace

extern "C"
{

// Display plugin entry point.
asr::ITileCallbackFactory* create_tile_callback_factory( const asr::ParamArray *params )
{
    return new HAPS::DisplayTileCallbackFactory( *params );
}

}