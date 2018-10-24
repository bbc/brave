#include <include/cef_app.h>

class BrowserApp : public CefApp
{
public:
  BrowserApp();

  virtual void OnBeforeCommandLineProcessing(
      const CefString &process_type,
      CefRefPtr<CefCommandLine> command_line) OVERRIDE;

  virtual void OnRegisterCustomSchemes(
    CefRawPtr<CefSchemeRegistrar> registrar) OVERRIDE;

  IMPLEMENT_REFCOUNTING(BrowserApp);
};

BrowserApp::BrowserApp() {}

void BrowserApp::OnBeforeCommandLineProcessing(
    const CefString &process_type,
    CefRefPtr<CefCommandLine> command_line)
{
  command_line->AppendSwitch("disable-gpu");
  command_line->AppendSwitch("disable-gpu-compositing");
  command_line->AppendSwitch("enable-begin-frame-scheduling");
  command_line->AppendSwitch("enable-system-flash");
  command_line->AppendSwitch("log-severity=disable");
}

void BrowserApp::OnRegisterCustomSchemes(
    CefRawPtr<CefSchemeRegistrar> registrar)
{
}

int main(int argc, char* argv[])
{
  CefMainArgs mainArgs(argc, argv);
  CefRefPtr<BrowserApp> app(new BrowserApp());
  return CefExecuteProcess(mainArgs, app.get(), NULL);
}