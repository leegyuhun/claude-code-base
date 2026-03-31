library PrinterScanLib;

uses
  Windows,
  Forms,
  uMainForm in 'Source\uMainForm.pas' {frmMain},
  uSNMP in 'Source\uSNMP.pas',
  uNetworkUtils in 'Source\uNetworkUtils.pas',
  uSubnetCalc in 'Source\uSubnetCalc.pas',
  uScanEngine in 'Source\uScanEngine.pas',
  uScanTypes in 'Source\uScanTypes.pas',
  uDLLExport in 'Source\uDLLExport.pas';

{$R *.res}

exports
  ShowPrinterScanner,
  StartPrinterScan;

begin
end.
