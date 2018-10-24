#ifndef CLIENT_H
#define	CLIENT_H

#include <gst/gstinfo.h>

#include <include/cef_client.h>
#include <include/cef_render_handler.h>

class Client : 
    public CefClient,
    public CefRenderHandler,
    public CefLifeSpanHandler
{
public:
    class Listener {
    public: 
        virtual bool GetViewRect(CefRect& rect) = 0;
        virtual void OnPaint(CefRenderHandler::PaintElementType type, const CefRenderHandler::RectList& rects, const void* buffer, int width, int height)  = 0;
    };
public:
    Client(Listener *listener);
    virtual ~Client();
    
    //Overrride
    virtual CefRefPtr<CefRenderHandler> GetRenderHandler() override {
        // Return the handler for off-screen rendering events.
        return this;
    }
    virtual CefRefPtr<CefLifeSpanHandler> GetLifeSpanHandler() override {
        // Return browser life span handler
        return this;
    }
    
    virtual bool GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) override;
    virtual void OnPaint(CefRefPtr<CefBrowser> browser, CefRenderHandler::PaintElementType type, const RectList& rects, const void* buffer, int width, int height) override;

    IMPLEMENT_REFCOUNTING(Client);
private:
    Listener* listener;
};

#endif	/* CLIENT_H */
