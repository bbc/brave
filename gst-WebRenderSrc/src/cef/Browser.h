#ifndef CEFBROWSER_H
#define	CEFBROWSER_H

#include <gst/gstinfo.h>

#include "include/cef_app.h"
#include "include/cef_client.h"
#include "Client.h"

/*
 * Application Structure
 *  Every CEF3 application has the same general structure.
 *  Provide an entry-point function that initializes CEF and runs either sub-process executable logic or the CEF message loop.
 *  Provide an implementation of CefApp to handle process-specific callbacks.
 *  Provide an implementation of CefClient to handle browser-instance-specific callbacks.
 *  Call CefBrowserHost::CreateBrowser() to create a browser instance and manage the browser life span using CefLifeSpanHandler.
 */

class Browser :
        public CefApp,
        public Client::Listener,
        public CefBrowserProcessHandler,
        public CefRenderProcessHandler
{
public:
        static Browser& getInstance()
        {
            static Browser instance;
            return instance;
        }
    
private:
        // Dont forget to declare these two. You want to make sure they
        // are unaccessable otherwise you may accidently get copies of
        // your singelton appearing.
    Browser();
        Browser(Browser const&);                  // Don't Implement
        void operator=(Browser const&);           // Don't implement

public:
    int Init(void *webRenderSrc, void* push_frame);
    void Run();
    int CreateFrame(std::string url, int width, int height);
    int End();
    virtual ~Browser();

    virtual void OnBeforeCommandLineProcessing(const CefString& process_type,CefRefPtr<CefCommandLine> command_line) override {
        command_line->AppendSwitch("disable-gpu");
        command_line->AppendSwitch("disable-gpu-compositing");
        command_line->AppendSwitch("enable-begin-frame-scheduling");
        command_line->AppendSwitch("enable-media-stream");
        command_line->AppendSwitchWithValue("disable-gpu-vsync", "gpu");
    }

    // CLient::Listner functions
    //From client listener
    virtual bool GetViewRect(CefRect& rect) override;
    virtual void OnPaint(CefRenderHandler::PaintElementType type, const CefRenderHandler::RectList& rects, const void* buffer, int width, int height) override;

    IMPLEMENT_REFCOUNTING(Browser);

private:
    bool inited;
     // Specify CEF global settings here.
    CefSettings settings;

    void *webRenderSrc;
    void (* push_frame)(void *webRenderSrc, const void *buffer, int width, int height);
};

#endif	/* CEFBROWSER_H */
