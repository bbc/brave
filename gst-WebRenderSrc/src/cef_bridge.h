#ifndef _CEF_BRIDGE_H_
#define _CEF_BRIDGE_H_

#include <stdint.h>
#include <gst/gstinfo.h>

#ifdef __cplusplus
extern "C" {
#endif

GST_EXPORT GstDebugCategory *gst_web_render_src_debug;
#define GST_CAT_DEFAULT gst_web_render_src_debug

struct cef_interface
{
    void *gstWebRenderSrc;
    void *push_frame;
    char *url;
    int width;
    int height;
};

void new_browser_instance(gpointer args);
void end_browser_instance();
void run_browser_message_loop(gpointer args);

#ifdef __cplusplus
}
#endif

#endif