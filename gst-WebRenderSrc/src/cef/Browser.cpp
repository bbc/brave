#include <include/internal/cef_types.h>
#include <include/cef_base.h>
#include "Browser.h"
#include "Client.h"
#include <signal.h>

Browser::Browser()
{
    //Y no tamos iniciados
    inited = 0;
}


/************************
* ~ Browser
* 	Destructor
*************************/
Browser::~Browser()
{
    //Check we have been correctly ended
    if (inited)
        //End it anyway
        End();
}


/************************
* Init
* 	
*************************/
int Browser::Init(void *webRenderSrc, void *push_frame)
{
    CefMainArgs main_args;
    CefRefPtr<Browser> app(this);

    // CEF applications have multiple sub-processes (render, plugin, GPU, etc)
    // that share the same executable. This function checks the command-line and,
    // if this is a sub-process, executes the appropriate logic.
    int exit_code = CefExecuteProcess(main_args, app.get(), NULL);

    if (exit_code >= 0) 
        // The sub-process has completed so return here.
        return exit_code;

    //Check not already inited
    if (inited)
        return exit_code;

    //Enable remote debugging
    settings.remote_debugging_port=2012;
    
    ///
    // Set to true (1) to enable windowless (off-screen) rendering support. Do not
    // enable this value if the application does not use windowless rendering as
    // it may reduce rendering performance on some systems.
    ///
    settings.windowless_rendering_enabled = true;

    ///
    // Since we are using gstreamer as the main process we need to give our
    // subprocess a different place to be executed from this stops cef
    // calling this file to runder the renders
    ///
    CefString(&settings.browser_subprocess_path).FromASCII("cefsubprocess");

    #if defined(OS_MACOSX)
    CefString(&settings.framework_dir_path).FromASCII("/usr/local/Frameworks/Chromium Embedded Framework.framework");
    #endif

    this->push_frame = (void (*)(void *webRenderSrc, const void *buffer, int width, int height)) push_frame;
    this->webRenderSrc = webRenderSrc;

    //Verbose logs	
    settings.log_severity = LOGSEVERITY_WARNING;

    // Initialize CEF for the browser process.
    CefInitialize(main_args, settings, app.get(), NULL);

    //I am inited
    inited = 1;

    //Return ok
    return 1;
}

/***************************
 * Run
 * 	Server running thread
 ***************************/
void Browser::Run()
{
    // Run the CEF message loop. This will block until CefQuitMessageLoop() is called.
    if (inited)
        CefDoMessageLoopWork();
}

/************************
* End
* 	End server and close all connections
*************************/
int Browser::End()
{
    //Check we have been inited
    if (!inited)
        //Do nothing
        return 0;

    //Stop thread
    inited = 0;

    //Quite message loop 
    CefQuitMessageLoop();

    // Shut down CEF.
    CefShutdown();

    return 0;
}

int Browser::CreateFrame(std::string url, int width, int height)
{
    // Information about the window that will be created including parenting, size, etc.
    CefWindowInfo info;
    
    info.width = width;
    info.height = height;

    info.windowless_rendering_enabled = true;
    
     // Client implements browser-level callbacks and RenderHandler
    CefRefPtr<Client> handler(new Client(this));

    // Specify CEF browser settings here.
    CefBrowserSettings browser_settings;

    //Set the refresh rate to 30fps
    browser_settings.windowless_frame_rate = 30;
    
    // Create the first browser window.
    CefBrowserHost::CreateBrowserSync(info, handler.get(), url, browser_settings, NULL);
    GST_INFO("CefBrowserHost::CreateBrowserSync");

    return 0;
}

void Browser::OnPaint(CefRenderHandler::PaintElementType type, const CefRenderHandler::RectList& rects, const void* buffer, int width, int height)
{
    push_frame(webRenderSrc, buffer, width, height);
}

bool Browser::GetViewRect(CefRect& rect)
{
    GST_INFO("Browser::GetViewRect");
    rect.Set(0, 0, 1280, 720);
    return true;
}

/*Off-Screen Rendering
 * With off-screen rendering CEF does not create a native browser window. 
 * Instead, CEF provides the host application with invalidated regions and a 
 * pixel buffer and the host application notifies CEF of mouse, keyboard and 
 * focus events. Off-screen rendering does not currently support accelerated 
 * compositing so performance may suffer as compared to a windowed browser.
 * Off-screen browsers will receive the same notifications as windowed browsers 
 * including the life span notifications described in the previous section.
 * To use off-screen rendering:
 *  Implement the CefRenderHandler interface. All methods are required unless otherwise indicated.
 *  Call CefWindowInfo::SetAsOffScreen() and optionally CefWindowInfo::SetTransparentPainting() before passing the CefWindowInfo structure to CefBrowserHost::CreateBrowser().
 *  If no parent window is passed to SetAsOffScreen some functionality like ontext menus may not be available.
 *  The CefRenderHandler::GetViewRect() method will be called to retrieve the desired view rectangle.
 *  The CefRenderHandler::OnPaint() method will be called to provide invalid regions and the updated pixel buffer.
 *  The cefclient application draws the buffer using OpenGL but your application can use whatever technique you prefer.
 *  To resize the browser call CefBrowserHost::WasResized(). This will result in a call to GetViewRect() to retrieve the new size followed by a call to OnPaint().
 *  Call the CefBrowserHost::SendXXX() methods to notify the browser of mouse, keyboard and focus events.
 *  Call CefBrowserHost::CloseBrowser() to destroy browser.
 */
