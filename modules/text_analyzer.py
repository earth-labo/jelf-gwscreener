"""
テキスト分析モジュール
"""
from typing import Dict, Any
import sys
import os

def analyze_text_content(ai_handler, text: str, system_prompt: str, 
                        criteria_sections: list) -> Dict[str, Any]:
    """
    テキストを分析
    
    Args:
        ai_handler: AIハンドラーインスタンス
        text: 分析対象テキスト
        system_prompt: システムプロンプト
        criteria_sections: 適用する診断基準セクション
        
    Returns:
        分析結果
    """
    user_prompt = f"""
【分析対象テキスト】
{text}

【適用する診断基準】
{', '.join(criteria_sections)}

【分析手順】
1. テキストを一文ずつ精査
2. 適用する診断基準に基づいてClimateWashを検出
3. 各違反項目について減点を計算
4. 具体的な是正案を提示

【重要】
- 文脈を考慮して判断
- 単語の出現だけでなく、主張の実証性を評価
- 日本語の婉曲表現に特に注意
"""
    
    return ai_handler.analyze_text(system_prompt, user_prompt)

def quick_check_text(text: str) -> Dict[str, Any]:
    """
    テキストの簡易チェック（AIを使わない高速チェック）
    
    Args:
        text: チェック対象テキスト
        
    Returns:
        簡易チェック結果
    """
    issues = []
    
    # 一般的・抽象的な気候主張のチェック
    ng_phrases = [
        "カーボンニュートラル", "気候中立", "CO2ゼロ", "ネットゼロ", 
        "エコ", "環境に優しい", "地球に優しい", "エコフレンドリー",
        "グリーン", "クリーン", "サステナブル", "持続可能"
    ]
    
    found_phrases = []
    for phrase in ng_phrases:
        if phrase in text:
            found_phrases.append(phrase)
    
    if found_phrases:
        issues.append({
            "type": "一般的・抽象的な表現",
            "phrases": found_phrases,
            "suggestion": "具体的な数値とデータで裏付けてください"
        })
    
    # オフセット関連のチェック
    offset_phrases = ["オフセット", "カーボンクレジット", "排出権", "カーボンオフセット"]
    found_offset = []
    for phrase in offset_phrases:
        if phrase in text:
            found_offset.append(phrase)
    
    if found_offset:
        issues.append({
            "type": "オフセット関連",
            "phrases": found_offset,
            "suggestion": "自社削減とオフセットを明確に区別してください"
        })
    
    # 曖昧な表現のチェック
    vague_phrases = ["取り組んでいます", "目指します", "努めます", "配慮", "検討中"]
    found_vague = []
    for phrase in vague_phrases:
        if phrase in text:
            found_vague.append(phrase)
    
    if found_vague:
        issues.append({
            "type": "曖昧な表現",
            "phrases": found_vague,
            "suggestion": "具体的な実績や計画を明示してください"
        })
    
    return {
        "has_issues": len(issues) > 0,
        "issues": issues,
        "issue_count": len(issues)
    }
