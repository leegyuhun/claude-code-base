unit uMainForm;
{
  메인 폼 유닛.
  스캔 설정 패널, 프린터 목록 ListView, 실시간 로그 패널을 포함한다.
  VCL 컴포넌트: TForm, TListView, TMemo, TEdit, TButton, TPanel 등.
}

interface

uses
  Windows, Messages, SysUtils, Classes, Graphics, Controls, Forms,
  Dialogs, ComCtrls, StdCtrls, ExtCtrls,
  uScanTypes, uScanEngine;

type
  TfrmMain = class(TForm)
    { 컴포넌트는 Sprint-02에서 DFM과 함께 구현 }
  private
    FScanEngine: TScanEngine;
    FSelectedIP: string;
  public
    property SelectedIP: string read FSelectedIP;
  end;

var
  frmMain: TfrmMain;

implementation

{$R *.dfm}

end.
