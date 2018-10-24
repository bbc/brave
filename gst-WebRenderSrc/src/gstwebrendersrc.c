/*
 * GStreamer
 * Copyright (C) 2005 Thomas Vander Stichele <thomas@apestaart.org>
 * Copyright (C) 2005 Ronald S. Bultje <rbultje@ronald.bitfreak.net>
 * Copyright (C) 2018  <<user@hostname.org>>
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 *
 * Alternatively, the contents of this file may be used under the
 * GNU Lesser General Public License Version 2.1 (the "LGPL"), in
 * which case the following provisions apply instead of the ones
 * mentioned above:
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#ifdef HAVE_CONFIG_H
#  include <config.h>
#endif

#include <gst/gst.h>
#include "gstwebrendersrc.h"
#include "cef_bridge.h"

GST_DEBUG_CATEGORY (gst_web_render_src_debug);
#define GST_CAT_DEFAULT gst_web_render_src_debug
#define SUPPORTED_GL_APIS (GST_GL_API_OPENGL | GST_GL_API_OPENGL3 | GST_GL_API_GLES2)
#define DEFAULT_IS_LIVE TRUE
#define SRC_VIDEO_CAPS GST_VIDEO_CAPS_MAKE("RGBA")
#define gst_web_render_src_parent_class parent_class

/* Filter signals and args */
enum
{
  PROP_0,
  PROP_URL,
  PROP_WIDTH,
  PROP_HEIGHT
};

#define DEFAULT_URL     "http://www.bbc.co.uk"
#define DEFAULT_WIDTH      1280
#define DEFAULT_HEIGHT     720

static GstStaticPadTemplate src_factory = GST_STATIC_PAD_TEMPLATE ("src",
    GST_PAD_SRC,
    GST_PAD_ALWAYS,
    GST_STATIC_CAPS (SRC_VIDEO_CAPS)
);

G_DEFINE_TYPE_WITH_CODE(GstWebRenderSrc, gst_web_render_src, GST_TYPE_PUSH_SRC,
                        GST_DEBUG_CATEGORY_INIT(gst_web_render_src_debug, "webrender", 0,
                        "debug category for cef element"));

/* basesrc methods */
static void set_property (GObject * object, guint prop_id, const GValue * value, GParamSpec * pspec);
static void get_property (GObject * object, guint prop_id, GValue * value, GParamSpec * pspec);
static gboolean is_seekable(GstBaseSrc *src);
static GstCaps * get_caps(GstBaseSrc *src, GstCaps *filter);
static gboolean start(GstBaseSrc *src);
static gboolean stop(GstBaseSrc *src);
static GstFlowReturn fill(GstPushSrc *src, GstBuffer *buf);

/* GObject vmethod implementations */

/* initialize the webrendersrc's class */
static void gst_web_render_src_class_init (GstWebRenderSrcClass * klass)
{
    GST_DEBUG("gst_web_render_src_init");

    GObjectClass *gobject_class = (GObjectClass *) klass;
    GstElementClass *gstelement_class = (GstElementClass *) klass;
    GstBaseSrcClass *basesrc_class = (GstBaseSrcClass *) klass;
    GstPushSrcClass *pushsrc_class = (GstPushSrcClass *) klass;

    gobject_class->set_property = set_property;
    gobject_class->get_property = get_property;

    basesrc_class->get_caps = get_caps;
    basesrc_class->is_seekable = is_seekable;
    basesrc_class->start = start;
    basesrc_class->stop = stop;

    pushsrc_class->fill = fill;

    g_object_class_install_property(gobject_class, PROP_URL, g_param_spec_string("url", "url", "website to render into video", DEFAULT_URL, G_PARAM_READWRITE | G_PARAM_STATIC_STRINGS));
    g_object_class_install_property(gobject_class, PROP_WIDTH, g_param_spec_uint("width", "width", "width of the internal chrome render", 0, G_MAXUINT, DEFAULT_WIDTH, G_PARAM_READWRITE));
    g_object_class_install_property(gobject_class, PROP_HEIGHT, g_param_spec_uint("height", "height", "height of the internal chrome render", 0, G_MAXUINT, DEFAULT_WIDTH, G_PARAM_READWRITE));

    gst_element_class_add_pad_template (gstelement_class, gst_static_pad_template_get (&src_factory));
    gst_element_class_set_details_simple(gstelement_class, "WebRenderSrc", "CEF BASED gstreamer video src", "Renders a HTML as a video Src", "silver@bbc.co.uk");
}

static void gst_web_render_src_init (GstWebRenderSrc * render)
{
    GST_DEBUG("gst_web_render_src_init");

    render->url         = DEFAULT_URL;
    render->width       = DEFAULT_WIDTH;
    render->height      = DEFAULT_HEIGHT;

    render->frames = g_async_queue_new_full ((GDestroyNotify) gst_buffer_unref);

    gst_base_src_set_format(GST_BASE_SRC(render), GST_FORMAT_TIME);
    gst_base_src_set_live(GST_BASE_SRC(render), DEFAULT_IS_LIVE);
    gst_base_src_set_do_timestamp(GST_BASE_SRC(render), TRUE);
}

static void set_property (GObject * object, guint prop_id, const GValue * value, GParamSpec * pspec)
{
    GstWebRenderSrc *render = GST_WEBRENDERSRC (object);

    switch (prop_id) {
        case PROP_URL:
            render->url = g_strdup(g_value_get_string(value));
            break;

        case PROP_WIDTH:
            render->width = g_value_get_uint(value);
        break;

        case PROP_HEIGHT:
            render->height = g_value_get_uint(value);
        break;

        default:
            G_OBJECT_WARN_INVALID_PROPERTY_ID (object, prop_id, pspec);
            break;
    }
}

static void get_property (GObject * object, guint prop_id, GValue * value, GParamSpec * pspec)
{
    GstWebRenderSrc *render = GST_WEBRENDERSRC (object);

    switch (prop_id) {
        case PROP_URL:
            g_value_set_string(value, render->url);
            break;

        case PROP_WIDTH:
            g_value_set_uint(value, render->width);
            break;

         case PROP_HEIGHT:
            g_value_set_uint(value, render->height);
            break;

        default:
            G_OBJECT_WARN_INVALID_PROPERTY_ID (object, prop_id, pspec);
            break;
    }
}

/* get caps from subclass */
static GstCaps * get_caps(GstBaseSrc *src, GstCaps *filter)
{
    GstWebRenderSrc *render = GST_WEBRENDERSRC (src);
    GstCaps *caps;

    GST_DEBUG_OBJECT(render, "get_caps");

    caps = gst_caps_new_simple("video/x-raw",
                                "format", G_TYPE_STRING, "BGRA",
                                "framerate", GST_TYPE_FRACTION, 30, 1,
                                "pixel-aspect-ratio", GST_TYPE_FRACTION, 1, 1,
                                "width", G_TYPE_INT, render->width,
                                "height", G_TYPE_INT, render->height,
                                NULL);

    return caps;
}

/* Mark this as false as this is a live src */
static gboolean is_seekable(GstBaseSrc *src)
{
    return FALSE;
}

static void push_frame(void *gstWebRenderSrc, const void *frame, int width, int height)
{
    GstWebRenderSrc *render = (GstWebRenderSrc *) gstWebRenderSrc;
    int size = width * height * 4;
    GstBuffer * buffer;

    if (size != (render->width * render->height * 4))
    {
        GST_ERROR("push_frame size mismatch %d != %d * %d * 4", size, render->width, render->height);
        return;
    }

    buffer = gst_buffer_new_allocate(NULL, size, NULL);

    if (buffer) {
        gst_buffer_fill(buffer, 0, frame, size);
        GST_INFO ("queue encoded data buffer %p (buffer: %zu bytes)", buffer, gst_buffer_get_size (buffer));
        g_async_queue_push (render->frames, buffer);
    } else {
        GST_ERROR("push_frame does not have buffer");
        return;
    }
}

static gboolean start(GstBaseSrc *src)
{
    GstWebRenderSrc *render = GST_WEBRENDERSRC (src);
    GST_DEBUG_OBJECT(render, "start");

    GST_INFO("creating new cef instance");
    struct cef_interface *ci = g_malloc(sizeof(struct cef_interface));

    ci->gstWebRenderSrc = render;
    gst_object_ref(render);

    ci->url = g_strdup(render->url);
    ci->width = render->width;
    ci->height = render->height;
    ci->push_frame = push_frame;

    render->n_frames = 0;

    new_browser_instance(ci);
    render->active_thread = g_thread_ref(g_thread_new("browser_loop", (GThreadFunc)run_browser_message_loop, ci));

    return TRUE;
}

static gboolean stop(GstBaseSrc *src)
{
    GstWebRenderSrc *render = GST_WEBRENDERSRC (src);
    GST_DEBUG_OBJECT(render, "stop");
    render->active_thread = NULL; 

    end_browser_instance();

    return TRUE;
}

static GstFlowReturn fill(GstPushSrc *src, GstBuffer *buffer)
{
    GstWebRenderSrc *self = GST_WEBRENDERSRC (src);
    GstBuffer *buf;

    int size = self->width * self->height * 4;

    GST_BUFFER_OFFSET (buffer) = self->n_frames;
    self->n_frames++;
    GST_BUFFER_OFFSET_END (buffer) = self->n_frames;
 
    while ((buf = g_async_queue_try_pop (self->frames))) {
        GST_INFO ("popped data buffer %p (%zu bytes)", buf, gst_buffer_get_size(buf));
        gst_buffer_copy_into(buffer, buf, GST_BUFFER_COPY_MEMORY, 0, size);
        gst_buffer_unref (buf);
    }

    return GST_FLOW_OK;
}

/* init the plugin into Gstreamer */
static gboolean plugin_init (GstPlugin * plugin)
{
   return gst_element_register(plugin, "webrendersrc", GST_RANK_NONE, GST_TYPE_WEBRENDERSRC);
}

/* PACKAGE: this is usually set by autotools depending on some _INIT macro
 * in configure.ac and then written into and defined in config.h, but we can
 * just set it ourselves here in case someone doesn't use autotools to
 * compile this code. GST_PLUGIN_DEFINE needs PACKAGE to be defined.
 */
#ifndef PACKAGE
#define PACKAGE "webrendersrc"
#endif
#ifndef VERSION
#define VERSION "0.0.1"
#endif
#ifndef PACKAGE_NAME
#define PACKAGE_NAME "gst_webrendersrc"
#endif

/* gstreamer looks for this structure to register webrendersrcs
 *
 * exchange the string 'Template webrendersrc' with your webrendersrc description
 */
GST_PLUGIN_DEFINE (
    GST_VERSION_MAJOR,
    GST_VERSION_MINOR,
    webrendersrc,
    "A plugin to render HTML5 into a video stream",
    plugin_init,
    VERSION,
    "LGPL",
    "GStreamer",
    "http://gstreamer.net/"
)
