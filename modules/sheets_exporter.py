"""
Googleスプレッドシート出力モジュール
"""
from typing import Dict, Any, Tuple
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

class SheetsExporter:
    """Googleスプレッドシートへのエクスポート"""
    
    def __init__(self, credentials_dict: Dict):
        """
        Args:
            credentials_dict: Google Cloud サービスアカウントの認証情報
        """
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.creds = Credentials.from_service_account_info(
            credentials_dict, scopes=scopes
        )
        self.client = gspread.authorize(self.creds)
        self.last_error = None  # 最後のエラーを保存
    
    def export_results(self, spreadsheet_id: str, worksheet_name: str,
                      results: Dict[str, Any]) -> bool:
        """
        診断結果をスプレッドシートに出力
        
        Args:
            spreadsheet_id: スプレッドシートID
            worksheet_name: ワークシート名
            results: 診断結果
            
        Returns:
            成功したかどうか
        """
        try:
            # スプレッドシートを開く
            try:
                sheet = self.client.open_by_key(spreadsheet_id)
            except gspread.exceptions.SpreadsheetNotFound:
                self.last_error = f"スプレッドシートが見つかりません: ID={spreadsheet_id}"
                return False
            except gspread.exceptions.APIError as e:
                self.last_error = f"Google Sheets API エラー: {str(e)}"
                return False
            
            # ワークシートを取得（なければ作成）
            try:
                worksheet = sheet.worksheet(worksheet_name)
            except gspread.exceptions.WorksheetNotFound:
                try:
                    worksheet = sheet.add_worksheet(
                        title=worksheet_name, 
                        rows=1000, 
                        cols=11
                    )
                    # ヘッダー行を追加
                    headers = [
                        "診断日時", "コンテンツタイプ", "診断対象", "適用指令", "診断バージョン",
                        "総合評価", "スコア", "違反項目数", "違反詳細", 
                        "是正提案", "まとめ"
                    ]
                    worksheet.append_row(headers)
                except gspread.exceptions.APIError as e:
                    self.last_error = f"ワークシート作成エラー: {str(e)}"
                    return False
            
            # データ行を準備
            row = [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                results.get('content_type', '不明'),
                results.get('content_sample', '')[:500],  # 診断対象（500文字まで）
                results.get('directives', '不明'),
                results.get('version', '不明'),
                results.get('overall_risk', '不明'),
                results.get('score', 0),
                len(results.get('violations', [])),
                self._format_violations(results.get('violations', [])),
                self._format_recommendations(results.get('recommendations', [])),
                results.get('summary', '')[:500]  # 500文字まで
            ]
            
            # 行を追加
            try:
                # 現在の行数を取得
                all_values = worksheet.get_all_values()
                next_row = len(all_values) + 1
                
                # 明示的に次の行に書き込む
                for col_idx, value in enumerate(row, start=1):
                    worksheet.update_cell(next_row, col_idx, value)
                
                # 書き込みを確認
                import time
                time.sleep(1)  # APIの反映を待つ
                
                updated_values = worksheet.get_all_values()
                if len(updated_values) >= next_row:
                    last_row = updated_values[next_row - 1]
                    
                    # 日時の確認（フォーマットの違いを許容）
                    # 少なくとも日付部分と分が一致していればOK
                    expected_datetime = row[0]  # "2025-12-18 04:18:03"
                    actual_datetime = last_row[0] if last_row else ""
                    
                    # 日付と時分が含まれていればOK（秒とゼロパディングは無視）
                    expected_parts = expected_datetime.split()  # ["2025-12-18", "04:18:03"]
                    if len(expected_parts) >= 2:
                        expected_date = expected_parts[0]
                        expected_time_parts = expected_parts[1].split(":")  # ["04", "18", "03"]
                        expected_hour_min = f"{int(expected_time_parts[0])}:{expected_time_parts[1]}"  # "4:18"
                        
                        # 実際のデータに日付と時分が含まれているか確認
                        if expected_date in actual_datetime and expected_hour_min in actual_datetime:
                            return True
                        else:
                            self.last_error = f"データが正しく追加されませんでした。期待: {expected_datetime}, 実際: {actual_datetime}"
                            return False
                    else:
                        # フォールバック: 最初の10文字（日付部分）が一致すればOK
                        if actual_datetime.startswith(expected_datetime[:10]):
                            return True
                        else:
                            self.last_error = f"データが正しく追加されませんでした。期待: {expected_datetime}, 実際: {actual_datetime}"
                            return False
                else:
                    self.last_error = f"データ追加後、行数が不足しています（期待: {next_row}, 実際: {len(updated_values)}）"
                    return False
                    
            except gspread.exceptions.APIError as e:
                self.last_error = f"データ追加エラー: {str(e)}"
                return False
            
        except Exception as e:
            self.last_error = f"予期しないエラー: {str(e)}"
            import traceback
            self.last_error += f"\n{traceback.format_exc()}"
            return False
    
    def get_last_error(self) -> str:
        """最後に発生したエラーを取得"""
        return self.last_error or "エラー情報なし"
    
    def _format_violations(self, violations: list) -> str:
        """違反項目をフォーマット"""
        if not violations:
            return "なし"
        
        formatted = []
        for v in violations[:5]:  # 最大5件
            formatted.append(
                f"[{v.get('category', '')}] {v.get('category_name', '')}: "
                f"{v.get('description', '')}（減点: {v.get('points_deducted', 0)}）"
            )
        
        if len(violations) > 5:
            formatted.append(f"...他{len(violations) - 5}件")
        
        return " | ".join(formatted)
    
    def _format_recommendations(self, recommendations: list) -> str:
        """是正提案をフォーマット"""
        if not recommendations:
            return "なし"
        
        formatted = []
        for r in recommendations[:3]:  # 最大3件
            formatted.append(
                f"{r.get('issue', '')}: "
                f"{r.get('current_expression', '')} → "
                f"{r.get('recommended_expression', '')}"
            )
        
        if len(recommendations) > 3:
            formatted.append(f"...他{len(recommendations) - 3}件")
        
        return " | ".join(formatted)

def load_credentials_from_streamlit_secrets(st):
    """
    Streamlit Secretsから認証情報を読み込み
    
    Args:
        st: Streamlitモジュール
        
    Returns:
        認証情報の辞書
    """
    try:
        return dict(st.secrets["gcp_service_account"])
    except Exception as e:
        return None
