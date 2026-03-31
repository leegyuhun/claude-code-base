program PrinterScanApp;

uses
  Forms,
  uMainForm in 'Source\uMainForm.pas' {frmMain},
  uSNMP in 'Source\uSNMP.pas',
  uNetworkUtils in 'Source\uNetworkUtils.pas',
  uSubnetCalc in 'Source\uSubnetCalc.pas',
  uScanEngine in 'Source\uScanEngine.pas',
  uScanTypes in 'Source\uScanTypes.pas';

{$R *.res}

begin
  Application.Initialize;
  Application.Title := 'Network Printer Scanner';
  Application.CreateForm(TfrmMain, frmMain);
  Application.Run;
end.
