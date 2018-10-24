#include "Client.h"

Client::Client(Listener* listener)
{ 
    //Store
    this->listener = listener;
}

Client::~Client()
{
}

bool Client::GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect)
{
    //Call listener
    return listener && listener->GetViewRect(rect);
}

void Client::OnPaint(CefRefPtr<CefBrowser>, CefRenderHandler::PaintElementType type, const RectList& rects, const void* buffer, int width, int height)
{
    GST_INFO("Browser::OnPaint %uX%u", width, height);

    if (type != PET_VIEW)
        return;

    //Call listener
    if (listener) listener->OnPaint(type, rects, buffer, width, height);
}