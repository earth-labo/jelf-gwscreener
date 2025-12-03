"""
評価・点数計算ロジック
"""
from typing import Dict, List, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.criteria import get_risk_level, RISK_LEVELS

def calculate_score(violations: List[Dict[str, Any]]) -> int:
    """
    違反項目から総合スコアを計算
    
    Args:
        violations: 違反項目のリスト
        
    Returns:
        総合スコア（0-100）
    """
    base_score = 100
    total_deduction = 0
    
    for violation in violations:
        if "points_deducted" in violation:
            total_deduction += violation["points_deducted"]
    
    final_score = max(0, base_score - total_deduction)
    return final_score

def evaluate_result(ai_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    AI分析結果を評価
    
    Args:
        ai_response: AIからの分析結果
        
    Returns:
        評価結果
    """
    # エラーチェック
    if "error" in ai_response:
        return {
            "success": False,
            "error": ai_response["error"],
            "details": ai_response.get("details", ""),
            "overall_risk": "エラー",
            "score": 0,
            "violations": [],
            "recommendations": [],
            "summary": f"エラーが発生しました: {ai_response.get('error', '不明なエラー')}"
        }
    
    # スコア計算
    violations = ai_response.get("violations", [])
    score = calculate_score(violations)
    
    # リスクレベル判定
    risk_level = get_risk_level(score)
    
    return {
        "success": True,
        "overall_risk": risk_level,
        "score": score,
        "violations": violations,
        "recommendations": ai_response.get("recommendations", []),
        "summary": ai_response.get("summary", ""),
        "risk_info": RISK_LEVELS[risk_level]
    }

def format_result_for_display(result: Dict[str, Any]) -> str:
    """
    結果を表示用にフォーマット
    
    Args:
        result: 評価結果
        
    Returns:
        フォーマットされた文字列
    """
    if not result.get("success", False):
        return f"❌ **エラー**: {result.get('error', '不明なエラー')}\n\n{result.get('details', '')}"
    
    risk_info = result.get("risk_info", {})
    color = risk_info.get("color", "")
    
    output = f"""
## {color} 総合評価: {result['overall_risk']}

**スコア**: {result['score']}/100

**評価**: {risk_info.get('description', '')}

---

### ⚠️ 検出された問題点 ({len(result['violations'])}件)

"""
    
    if result['violations']:
        for i, violation in enumerate(result['violations'], 1):
            output += f"""
**{i}. {violation.get('category_name', '不明な項目')}** (項目 {violation.get('category', '')})

- **リスクレベル**: {violation.get('risk_level', 'Unknown')}
- **減点**: {violation.get('points_deducted', 0)}点
- **問題内容**: {violation.get('description', '')}
- **該当表現**: 「{violation.get('evidence', '')}」

---
"""
    else:
        output += "\n問題は検出されませんでした。\n\n"
    
    output += "\n### 💡 是正提案\n\n"
    
    if result['recommendations']:
        for i, rec in enumerate(result['recommendations'], 1):
            output += f"""
**{i}. {rec.get('issue', '問題')}**

❌ **現在の表現**:  
「{rec.get('current_expression', '')}」

✅ **推奨する表現**:  
「{rec.get('recommended_expression', '')}」

📝 **理由**:  
{rec.get('explanation', '')}

---
"""
    else:
        output += "\n是正の必要はありません。\n\n"
    
    output += f"\n### 📋 まとめ\n\n{result['summary']}\n"
    
    return output
