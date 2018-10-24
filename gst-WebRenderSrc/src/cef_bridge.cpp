#include <unistd.h>

#include "cef_bridge.h"
#include "cef/Browser.h"

namespace
{
    static gint message_loop_running = 0;
}

void new_browser_instance(gpointer args)
{
    Browser& browser = Browser::getInstance();
    struct cef_interface *cb = (struct cef_interface *)args;

    browser.Init(cb->gstWebRenderSrc, cb->push_frame);

    g_atomic_int_set(&message_loop_running, 1);

    browser.CreateFrame(cb->url, cb->width, cb->height);
}

void end_browser_instance()
{
    g_atomic_int_set(&message_loop_running, 0);
    Browser::getInstance().End();
}

static bool _inner_browser_run(void)
{
    if (g_atomic_int_get(&message_loop_running)) {
        Browser::getInstance().Run();
        return true;
    } else {
        return false;
    }
}

void run_browser_message_loop(gpointer args)
{
    g_idle_add((GSourceFunc)_inner_browser_run, NULL);
}
