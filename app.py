"""
ClimateWash診断ツール - 全機能統合版（YouTube安全モード＋Whisper文字起こし対応）
"""
import streamlit as st
import sys
import os
from datetime import datetime
import json
import re
import tempfile
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# 自分のモジュールをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.ai_handler import AIHandler
from modules.evaluator import evaluate_result, format_result_for_display, calculate_score
from modules.text_analyzer import analyze_text_content, quick_check_text
from modules.image_analyzer import analyze_image_content, get_image_info
from modules.pdf_analyzer import analyze_pdf_content, get_pdf_info
from modules.web_analyzer import analyze_web_content, get_web_info
from modules.sheets_exporter import SheetsExporter, load_credentials_from_streamlit_secrets
from modules.pdf_reporter import generate_pdf_report
from config.criteria import VERSIONS, get_criteria_sections, EXAMPLE_LIBRARY

# ページ設定
st.set_page_config(
    page_title="ClimateWash診断ツール",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッション状態
if "diagnosis_history" not in st.session_state:
    st.session_state.diagnosis_history = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None


# -----------------------------
# 共通ユーティリティ
# -----------------------------
def load_system_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_youtube_id(url: str):
    """いろいろな形式の YouTube URL から video_id を抜き出す"""
    patterns = [
        r"v=([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"youtube\.com/embed/([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def fetch_youtube_subtitles(video_id: str):
    """
    YouTube 字幕取得
    - 日本語自動 → 日本語手動 → 英語自動 → 英語手動 の順で探す
    """
    try:
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)

        # 日本語（自動）
        try:
            t = transcripts.find_generated_transcript(['ja']).fetch()
            return " ".join(x["text"] for x in t)
        except Exception:
            pass

        # 日本語（手動）
        try:
            t = transcripts.find_manually_created_transcript(['ja']).fetch()
            return " ".join(x["text"] for x in t)
        except Exception:
            pass

        # 英語（自動）
        try:
            t = transcripts.find_generated_transcript(['en']).fetch()
            return " ".join(x["text"] for x in t)
        except Exception:
            pass

        # 英語（手動）
        try:
            t = transcripts.find_manually_created_transcript(['en']).fetch()
            return " ".join(x["text"] for x in t)
        except Exception:
            pass

        return None

    except (TranscriptsDisabled, NoTranscriptFound):
        return None
    except Exception:
        return None


def transcribe_video_with_openai(video_bytes: bytes, api_key: str):
    """
    Whisper（新しい openai-python）で動画を文字起こしする。
    GPT-4系（OpenAIモデル）を選択した時のみ利用する想定。
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # 一時ファイルへ保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="text"
                )
            return str(transcript)
        finally:
            os.remove(tmp_path)

    except Exception:
        return None


# -----------------------------
# メインアプリ
# -----------------------------
def main():
    # ヘッダー
    st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(90deg, #2E7D32 0%, #43A047 100%); border-radius: 10px;'>
        <h1 style='color: white; margin: 0;'>🌍 ClimateWash診断ツール</h1>
        <p style='color: white; margin: 10px 0 0 0;'>EU指令準拠 AI自動診断システム</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # サイドバー
    with st.sidebar:
        st.markdown("## ⚙️ 設定")

        # モデル選択
        model_type = st.radio(
            "使用するAIモデル",
            ["Claude (Sonnet 4.5)", "ChatGPT (GPT-4)"],
        )
        model_key = "claude" if "Claude" in model_type else "openai"

        # APIキー
        api_key = None
        if model_key == "claude":
            api_key = st.secrets.get("ANTHROPIC_API_KEY")
        else:
            api_key = st.secrets.get("OPENAI_API_KEY")
        if not api_key:
            api_key = st.text_input("API Key", type="password")

        st.markdown("---")

        # 指令設定
        green_claims_directive = st.checkbox("グリーンクレーム指令案（推奨）", value=True)
        directive_label = "両指令" if green_claims_directive else "エンパワメント指令のみ"

        st.markdown("---")

        # バージョン
        version_options = {
            "v1": VERSIONS["v1"]["name"],
            "v2": VERSIONS["v2"]["name"],
            "v3": VERSIONS["v3"]["name"],
        }
        selected_version = st.radio(
            "診断基準バージョン",
            list(version_options.keys()),
            index=2,
            format_func=lambda x: version_options[x],
        )

        st.markdown("---")

        # Sheets設定
        with st.expander("📊 Google Sheets設定（任意）"):
            spreadsheet_id = st.text_input("スプレッドシートID")
            worksheet_name = st.text_input("ワークシート名", value="診断結果")

        st.markdown("---")

        # 履歴 / 例文
        if st.button("📊 診断履歴を見る"):
            st.session_state.show_history = True
        if st.button("💡 表現例を見る"):
            st.session_state.show_examples = True

    # 例文
    if st.session_state.get("show_examples", False):
        show_example_library()
        if st.button("閉じる"):
            st.session_state.show_examples = False
        return

    # 履歴
    if st.session_state.get("show_history", False):
        show_diagnosis_history()
        if st.button("閉じる"):
            st.session_state.show_history = False
        return

    # タブ
    tabs = st.tabs([
        "📝 テキスト",
        "🖼️ 画像",
        "📄 PDF",
        "🎬 動画（YouTube＋ローカル安全モード）",
        "🌐 Webサイト"
    ])

    system_prompt = load_system_prompt()
    criteria_sections = get_criteria_sections(selected_version, green_claims_directive)

    with tabs[0]:
        handle_text_analysis(api_key, model_key, system_prompt, criteria_sections,
                             selected_version, directive_label,
                             spreadsheet_id, worksheet_name)

    with tabs[1]:
        handle_image_analysis(api_key, model_key, system_prompt, criteria_sections,
                              selected_version, directive_label,
                              spreadsheet_id, worksheet_name)

    with tabs[2]:
        handle_pdf_analysis(api_key, model_key, system_prompt, criteria_sections,
                            selected_version, directive_label,
                            spreadsheet_id, worksheet_name)

    with tabs[3]:
        handle_video_safe(api_key, model_key, system_prompt, criteria_sections,
                          selected_version, directive_label,
                          spreadsheet_id, worksheet_name)

    with tabs[4]:
        handle_web_analysis(api_key, model_key, system_prompt, criteria_sections,
                            selected_version, directive_label,
                            spreadsheet_id, worksheet_name)


# -----------------------------
# 各診断ハンドラ
# -----------------------------
def handle_text_analysis(api_key, model_key, system_prompt, criteria_sections,
                         version, directive_label, spreadsheet_id, worksheet_name):
    st.markdown("### 📝 テキスト診断")

    text_input = st.text_area(
        "テキスト入力",
        height=200,
        placeholder="例：当社の製品はカーボンニュートラルです…"
    )

    # 簡易チェック
    if text_input and len(text_input) > 10:
        with st.expander("⚡ クイックチェック（簡易診断）"):
            quick_result = quick_check_text(text_input)
            if quick_result["has_issues"]:
                st.warning(f"⚠️ {quick_result['issue_count']} 種類の潜在的問題を検出")
                for issue in quick_result["issues"]:
                    st.markdown(f"**{issue['type']}**: {', '.join(issue['phrases'])}")
                    st.caption(f"💡 {issue['suggestion']}")
            else:
                st.success("明らかな問題は検出されませんでした（詳細分析推奨）")

    col1, col2 = st.columns([1, 4])
    with col1:
        btn = st.button("🔍 診断開始", type="primary")
    with col2:
        if st.button("🗑️ クリア"):
            st.rerun()

    if not btn:
        return

    if not api_key:
        st.error("APIキーを入力してください")
        return
    if not text_input or len(text_input) < 10:
        st.error("10文字以上のテキストを入力してください")
        return

    with st.spinner("AI分析中…"):
        try:
            ai_handler = AIHandler(model_key, api_key)
            ai_response = analyze_text_content(
                ai_handler, text_input, system_prompt, criteria_sections
            )
            result = evaluate_result(ai_response)
            result["content_type"] = "テキスト"
            result["version"] = version
            result["directives"] = directive_label
            result["content_sample"] = text_input[:200]

            st.session_state.current_result = result
            st.session_state.diagnosis_history.append({
                "timestamp": datetime.now(),
                "type": "テキスト",
                "result": result,
            })
        except Exception as e:
            st.error(f"エラー: {str(e)}")
            return

    display_result(result, spreadsheet_id, worksheet_name)


def handle_image_analysis(api_key, model_key, system_prompt, criteria_sections,
                          version, directive_label, spreadsheet_id, worksheet_name):
    st.markdown("### 🖼️ 画像診断")

    uploaded_file = st.file_uploader(
        "画像ファイル",
        type=["png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed"
    )

    if not uploaded_file:
        return

    st.image(uploaded_file, caption="アップロード画像", use_container_width=True)
    image_data = uploaded_file.read()
    info = get_image_info(image_data)

    if "error" not in info:
        st.markdown("**画像情報:**")
        st.write(f"- サイズ: {info['width']} × {info['height']}")
        st.write(f"- フォーマット: {info['format']}")
        st.write(f"- ファイルサイズ: {info['size_kb']:.1f} KB")

    col1, col2 = st.columns([1, 4])
    with col1:
        btn = st.button("🔍 診断", type="primary")
    with col2:
        if st.button("🗑️ クリア"):
            st.rerun()

    if not btn:
        return

    if not api_key:
        st.error("APIキーを入力してください")
        return

    with st.spinner("AI分析中…"):
        try:
            ai_handler = AIHandler(model_key, api_key)
            ai_response = analyze_image_content(
                ai_handler, image_data, system_prompt, criteria_sections
            )
            result = evaluate_result(ai_response)
            result["content_type"] = "画像"
            result["version"] = version
            result["directives"] = directive_label
            result["content_sample"] = f"画像ファイル: {uploaded_file.name}"

            st.session_state.current_result = result
            st.session_state.diagnosis_history.append({
                "timestamp": datetime.now(),
                "type": "画像",
                "result": result,
            })
        except Exception as e:
            st.error(f"エラー: {str(e)}")
            return

    display_result(result, spreadsheet_id, worksheet_name)


def handle_pdf_analysis(api_key, model_key, system_prompt, criteria_sections,
                        version, directive_label, spreadsheet_id, worksheet_name):
    st.markdown("### 📄 PDF診断")

    uploaded_file = st.file_uploader(
        "PDFファイル",
        type=["pdf"],
        label_visibility="collapsed"
    )

    if not uploaded_file:
        return

    pdf_data = uploaded_file.read()
    info = get_pdf_info(pdf_data)

    if "error" not in info:
        st.markdown("**PDF情報:**")
        st.write(f"- ページ数: {info['page_count']}")
        st.write(f"- ファイルサイズ: {info['size_kb']:.1f} KB")

    col1, col2 = st.columns([1, 4])
    with col1:
        btn = st.button("🔍 診断", type="primary")
    with col2:
        if st.button("🗑️ クリア"):
            st.rerun()

    if not btn:
        return

    if not api_key:
        st.error("APIキーを入力してください")
        return

    with st.spinner("AI分析中…"):
        try:
            ai_handler = AIHandler(model_key, api_key)
            ai_response = analyze_pdf_content(
                ai_handler, pdf_data, system_prompt, criteria_sections
            )
            result = evaluate_result(ai_response)
            result["content_type"] = "PDF"
            result["version"] = version
            result["directives"] = directive_label
            result["content_sample"] = f"PDFファイル: {uploaded_file.name}"

            st.session_state.current_result = result
            st.session_state.diagnosis_history.append({
                "timestamp": datetime.now(),
                "type": "PDF",
                "result": result,
            })
        except Exception as e:
            st.error(f"エラー: {str(e)}")
            return

    display_result(result, spreadsheet_id, worksheet_name)


def handle_web_analysis(api_key, model_key, system_prompt, criteria_sections,
                        version, directive_label, spreadsheet_id, worksheet_name):
    st.markdown("### 🌐 Webサイト診断")

    url_input = st.text_input(
        "URL",
        placeholder="https://example.com/sustainability",
    )

    if not url_input:
        return

    if not url_input.startswith(("http://", "https://")):
        st.warning("URLは http:// または https:// で始めてください")
        return

    with st.expander("🔍 サイト情報を確認"):
        with st.spinner("情報取得中…"):
            info = get_web_info(url_input)
            if "error" not in info:
                st.markdown(f"**タイトル:** {info['title']}")
                st.markdown(f"**説明:** {info['description'][:200]}...")
                st.markdown(f"**テキスト量:** {info['text_length']} 文字")
                st.markdown(f"**画像数:** {info['image_count']} 枚")
            else:
                st.error(info["error"])

    col1, col2 = st.columns([1, 4])
    with col1:
        btn = st.button("🔍 診断", type="primary")
    with col2:
        if st.button("🗑️ クリア"):
            st.rerun()

    if not btn:
        return

    if not api_key:
        st.error("APIキーを入力してください")
        return

    with st.spinner("AI分析中…"):
        try:
            ai_handler = AIHandler(model_key, api_key)
            ai_response = analyze_web_content(
                ai_handler, url_input, system_prompt, criteria_sections
            )
            result = evaluate_result(ai_response)
            result["content_type"] = "Webサイト"
            result["version"] = version
            result["directives"] = directive_label
            result["content_sample"] = url_input

            st.session_state.current_result = result
            st.session_state.diagnosis_history.append({
                "timestamp": datetime.now(),
                "type": "Webサイト",
                "result": result,
            })
        except Exception as e:
            st.error(f"エラー: {str(e)}")
            return

    display_result(result, spreadsheet_id, worksheet_name)


def handle_video_safe(api_key, model_key, system_prompt, criteria_sections,
                      version, directive_label, spreadsheet_id, worksheet_name):
    st.markdown("### 🎬 動画診断（YouTube＋ローカル安全モード）")
    st.markdown("YouTube動画は埋め込み＋字幕テキスト、ローカル動画はWhisper文字起こしで分析します。")

    tab_url, tab_file = st.tabs(["🎥 YouTube URL から分析", "📁 手元の動画ファイルから分析"])

    transcript_source_label = None

    # --- YouTube タブ ---
    with tab_url:
        youtube_url = st.text_input(
            "YouTubeのURL",
            placeholder="https://www.youtube.com/watch?v=XXXXXXX"
        )

        video_id = None
        if youtube_url:
            video_id = extract_youtube_id(youtube_url)
            if not video_id:
                st.error("YouTube URL が正しくありません。")
            else:
                embed_url = f"https://www.youtube.com/embed/{video_id}"
                st.markdown("#### ▶ 動画プレビュー")
                st.video(embed_url)
                transcript_source_label = f"YouTube: {youtube_url}"

        st.markdown("---")

        # 字幕自動取得
        if video_id and st.button("🎯 YouTube字幕を自動取得する", type="primary"):
            with st.spinner("字幕を検索しています..."):
                auto_caption = fetch_youtube_subtitles(video_id)
            if auto_caption:
                st.success("字幕を取得しました")
                st.session_state["auto_caption"] = auto_caption
            else:
                st.error("利用可能な字幕が見つかりませんでした。")

    # --- ローカル動画タブ ---
    with tab_file:
        uploaded_file = st.file_uploader(
            "動画ファイル（mp4, mov, m4a, mp3, wavなど）",
            type=["mp4", "mov", "m4a", "mp3", "wav"],
            help="最大数分程度までを推奨します。",
        )

        if uploaded_file:
            try:
                st.video(uploaded_file)
            except Exception:
                st.caption("この形式はブラウザでプレビューできない場合があります。")

            st.markdown("#### 🔊 自動文字起こし（Whisper）")

            if model_key != "openai":
                st.info("自動文字起こしは ChatGPT (GPT-4) 選択時のみ利用できます。")
            else:
                if st.button("🎯 この動画から文字起こしする", key="transcribe_local_video"):
                    uploaded_file.seek(0)
                    video_bytes = uploaded_file.read()
                    with st.spinner("Whisper で文字起こし中…"):
                        text = transcribe_video_with_openai(video_bytes, api_key)
                    if text:
                        st.success("文字起こしが完了しました")
                        st.session_state["auto_caption"] = text
                        transcript_source_label = f"ローカル動画ファイル: {uploaded_file.name}"
                    else:
                        st.error("文字起こしに失敗しました。")

    # --- 共通：テキスト編集＆診断 ---
    st.markdown("---")
    st.subheader("📝 字幕 / 説明文テキスト（必要に応じて編集可）")

    caption_text = st.text_area(
        "字幕・スクリプト・説明文",
        value=st.session_state.get("auto_caption", ""),
        height=250,
        placeholder="YouTube字幕、自動文字起こし結果、または自分で用意したスクリプトを貼り付けてください"
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        btn = st.button("🔍 診断開始", type="primary")
    with col2:
        if st.button("🗑️ クリア"):
            st.session_state["auto_caption"] = ""
            st.rerun()

    if not btn:
        return

    if not api_key:
        st.error("APIキーを入力してください")
        return

    if not caption_text.strip():
        st.error("字幕または説明文テキストを入力してください")
        return

    with st.spinner("AI がテキスト内容を分析中です…"):
        try:
            ai_handler = AIHandler(model_key, api_key)
            ai_response = analyze_text_content(
                ai_handler, caption_text, system_prompt, criteria_sections
            )

            result = evaluate_result(ai_response)
            result["content_type"] = "動画スクリプト（字幕・文字起こし）"
            result["version"] = version
            result["directives"] = directive_label
            result["content_sample"] = caption_text[:200]
            if transcript_source_label:
                result["source"] = transcript_source_label

            st.session_state.current_result = result
            st.session_state.diagnosis_history.append({
                "timestamp": datetime.now(),
                "type": "動画スクリプト",
                "result": result,
            })
        except Exception as e:
            st.error(f"エラー: {str(e)}")
            return

    display_result(result, spreadsheet_id, worksheet_name)


# -----------------------------
# 結果表示・履歴・例文
# -----------------------------
def display_result(result, spreadsheet_id, worksheet_name):
    st.markdown("---")
    st.markdown("## 📊 診断結果")

    if not result.get("success", False):
        st.error(f"❌ {result.get('error', '不明なエラー')}")
        if "details" in result:
            st.error(result["details"])
        return

    risk_info = result.get("risk_info", {})
    color = risk_info.get("color", "")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("総合評価", f"{color} {result['overall_risk']}")
    with col2:
        st.metric("スコア", f"{result['score']}/100")
    with col3:
        st.metric("違反項目数", f"{len(result['violations'])}件")

    st.info(f"📝 {risk_info.get('description', '')}")

    formatted = format_result_for_display(result)
    st.markdown(formatted)

    col1, col2, col3 = st.columns(3)

    # PDF
    with col1:
        try:
            pdf_data = generate_pdf_report(result)
            st.download_button(
                "📄 PDFレポートをダウンロード",
                data=pdf_data,
                file_name=f"climatewash_report_{datetime.now():%Y%m%d_%H%M%S}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"PDF生成エラー: {e}")

    # JSON
    with col2:
        json_data = json.dumps(result, ensure_ascii=False, indent=2)
        st.download_button(
            "📥 JSON結果をダウンロード",
            data=json_data,
            file_name=f"climatewash_result_{datetime.now():%Y%m%d_%H%M%S}.json",
            mime="application/json",
            use_container_width=True,
        )

    # Google Sheets
    with col3:
        if spreadsheet_id and worksheet_name:
            if st.button("📊 Google Sheetsに出力", use_container_width=True):
                try:
                    creds = load_credentials_from_streamlit_secrets(st)
                    if creds:
                        exporter = SheetsExporter(creds)
                        ok = exporter.export_results(spreadsheet_id, worksheet_name, result)
                        if ok:
                            st.success("スプレッドシートに出力しました")
                        else:
                            st.error("出力に失敗しました")
                    else:
                        st.error("Google認証情報が設定されていません")
                except Exception as e:
                    st.error(f"エラー: {e}")
        else:
            st.caption("スプレッドシート出力にはIDとシート名の設定が必要です")


def show_example_library():
    st.markdown("## 💡 適切な表現例ライブラリ")
    st.markdown("EU指令に準拠した適切な表現例を参照できます。")

    for category, examples in EXAMPLE_LIBRARY.items():
        with st.expander(f"📚 {category}"):
            for i, example in enumerate(examples, 1):
                st.markdown(f"### 例 {i}")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**❌ NG表現:**")
                    st.error(example["ng"])
                with col2:
                    st.markdown("**✅ OK表現:**")
                    st.success(example["ok"])

                st.markdown(f"**📝 理由:** {example['reason']}")
                st.markdown("---")


def show_diagnosis_history():
    st.markdown("## 📊 診断履歴")

    history = st.session_state.diagnosis_history
    if not history:
        st.info("まだ診断履歴がありません。")
        return

    history = sorted(history, key=lambda x: x["timestamp"], reverse=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("総診断数", len(history))
    with col2:
        avg_score = sum(h["result"]["score"] for h in history) / len(history)
        st.metric("平均スコア", f"{avg_score:.1f}")
    with col3:
        high_risk_count = sum(1 for h in history if h["result"]["overall_risk"] == "High Risk")
        st.metric("High Risk件数", high_risk_count)
    with col4:
        type_counts = {}
        for h in history:
            t = h["type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        most_common = max(type_counts.items(), key=lambda x: x[1])[0]
        st.metric("最多診断タイプ", most_common)

    st.markdown("---")
    st.markdown("### 📋 診断リスト")

    for entry in history:
        ts = entry["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        r = entry["result"]
        with st.expander(f"{ts} - {entry['type']} - {r['overall_risk']} ({r['score']}点)"):
            st.markdown(format_result_for_display(r))


if __name__ == "__main__":
    main()
