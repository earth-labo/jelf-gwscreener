"""
Webサイト分析モジュール
"""
from typing import Dict, Any, List
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def fetch_webpage(url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Webページを取得
    
    Args:
        url: URL
        timeout: タイムアウト（秒）
        
    Returns:
        ページデータ
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        return {
            "success": True,
            "content": response.content,
            "text": response.text,
            "status_code": response.status_code,
            "encoding": response.encoding
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def extract_text_from_html(html: str) -> str:
    """
    HTMLからテキストを抽出
    
    Args:
        html: HTMLコンテンツ
        
    Returns:
        抽出されたテキスト
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # スクリプトとスタイルを削除
        for script in soup(["script", "style"]):
            script.decompose()
        
        # テキストを取得
        text = soup.get_text(separator='\n')
        
        # 空行を削除
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        
        return '\n'.join(lines)
    except Exception as e:
        return f"テキスト抽出エラー: {str(e)}"

def extract_images_from_html(html: str, base_url: str) -> List[str]:
    """
    HTMLから画像URLを抽出
    
    Args:
        html: HTMLコンテンツ
        base_url: ベースURL
        
    Returns:
        画像URLのリスト
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # 相対URLを絶対URLに変換
                absolute_url = urljoin(base_url, src)
                images.append(absolute_url)
        
        return images[:10]  # 最大10枚
    except Exception as e:
        return []

def analyze_css_colors(html: str) -> Dict[str, Any]:
    """
    CSSから色彩スキームを分析
    
    Args:
        html: HTMLコンテンツ
        
    Returns:
        色彩分析結果
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # 環境関連色のカウント
        green_count = 0
        blue_count = 0
        
        # style属性をチェック
        for tag in soup.find_all(style=True):
            style = tag['style'].lower()
            if 'green' in style or '#0f0' in style or 'rgb(0,' in style:
                green_count += 1
            if 'blue' in style or '#00f' in style or 'rgb(0,0,' in style:
                blue_count += 1
        
        # classやidに "green", "eco", "sustainable" などが含まれるかチェック
        eco_classes = 0
        for tag in soup.find_all(class_=True):
            classes = ' '.join(tag['class']).lower()
            if any(word in classes for word in ['green', 'eco', 'sustainable', 'climate']):
                eco_classes += 1
        
        return {
            "green_elements": green_count,
            "blue_elements": blue_count,
            "eco_classes": eco_classes
        }
    except Exception as e:
        return {"error": str(e)}

def analyze_web_content(ai_handler, url: str, system_prompt: str,
                       criteria_sections: list) -> Dict[str, Any]:
    """
    Webサイトを分析
    
    Args:
        ai_handler: AIハンドラーインスタンス
        url: 分析対象URL
        system_prompt: システムプロンプト
        criteria_sections: 適用する診断基準セクション
        
    Returns:
        分析結果
    """
    # Webページを取得
    page_data = fetch_webpage(url)
    
    if not page_data.get("success", False):
        return {
            "error": "Webページ取得失敗",
            "details": page_data.get("error", "")
        }
    
    # テキスト抽出
    text = extract_text_from_html(page_data["text"])
    
    # 画像URL抽出
    image_urls = extract_images_from_html(page_data["text"], url)
    
    # 色彩分析
    color_analysis = analyze_css_colors(page_data["text"])
    
    # テキスト分析
    user_prompt = f"""
【分析対象】
Webサイト: {url}

【抽出されたテキスト】
{text[:5000]}  # 最初の5000文字

【画像数】
{len(image_urls)}枚の画像を検出

【色彩分析】
- 緑色の要素: {color_analysis.get('green_elements', 0)}個
- 青色の要素: {color_analysis.get('blue_elements', 0)}個
- 環境関連クラス名: {color_analysis.get('eco_classes', 0)}個

【適用する診断基準】
{', '.join(criteria_sections)}

【分析手順】
1. テキストコンテンツを診断基準に基づいて分析
2. 画像の使用状況を評価
3. 色彩スキームが環境イメージを過剰に演出していないかチェック
4. サイト全体の一貫性を評価

【重要】
- Webサイトは公開情報であり、企業の公式見解として扱われる
- メタデータやAlt属性も考慮
- ページ全体のトーン・マナーを評価
"""
    
    result = ai_handler.analyze_text(system_prompt, user_prompt)
    
    # 画像URLがある場合は、最初の画像をダウンロードして分析
    if image_urls:
        try:
            img_response = requests.get(image_urls[0], timeout=10)
            if img_response.status_code == 200:
                image_prompt = """
【補足分析】
Webサイトに掲載されている代表的な画像です。ビジュアル要素を分析してください。
"""
                image_result = ai_handler.analyze_image(system_prompt, image_prompt, 
                                                       img_response.content)
                # 画像分析結果をマージ
                if "violations" in image_result and "violations" in result:
                    result["violations"].extend(image_result.get("violations", []))
        except:
            pass  # 画像分析が失敗しても続行
    
    return result

def get_web_info(url: str) -> Dict[str, Any]:
    """
    Webサイトの基本情報を取得
    
    Args:
        url: URL
        
    Returns:
        Webサイト情報
    """
    try:
        page_data = fetch_webpage(url)
        
        if not page_data.get("success", False):
            return {"error": page_data.get("error", "")}
        
        soup = BeautifulSoup(page_data["text"], 'lxml')
        
        # メタデータを取得
        title = soup.title.string if soup.title else "No title"
        description = ""
        keywords = ""
        
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            description = meta_desc.get("content", "")
        
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords:
            keywords = meta_keywords.get("content", "")
        
        return {
            "url": url,
            "title": title,
            "description": description,
            "keywords": keywords,
            "text_length": len(extract_text_from_html(page_data["text"])),
            "image_count": len(extract_images_from_html(page_data["text"], url))
        }
    except Exception as e:
        return {
            "error": f"Webサイト情報の取得に失敗: {str(e)}"
        }
