from __future__ import annotations

from typing import Dict, Any, List
from pathlib import Path

import streamlit as st

# ★ ここがポイント：相対インポート（先頭に .. がついていること！）
from ..domain.invoice import Invoice
from ..services.ocr_service import OcrService
from ..services.excel_service import ExcelService


def _init_session_state() -> None:
    defaults = {
        "pdf_files": [],
        "output_file": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_main_page(cfg: Dict[str, Any]) -> None:
    """
    メイン画面（1ページ構成）。
    - 左: PDF アップロード
    - 中: 実行ボタン
    - 右: 結果プレビュー & Excel ダウンロード
    """
    _init_session_state()

    st.title("見積プロトタイプ｜PDF 明細 → テンプレExcelへ自動反映")

    left, mid, right = st.columns([4, 1.5, 4])

    # Service は1回だけ生成
    ocr_service = OcrService(cfg)
    excel_service = ExcelService(cfg)

    # ① PDF アップロード
    with left:
        st.subheader("① PDFをアップロード")
        pdf_files = st.file_uploader(
            "PDFをアップロード（複数選択可・一個ずつでもOK）",
            type=["pdf"],
            accept_multiple_files=True,
            key="pdf_uploader",
        )

        if pdf_files:
            st.session_state.pdf_files = []
            for f in pdf_files:
                st.session_state.pdf_files.append(
                    {
                        "name": f.name,
                        "status": "未処理",
                        "invoice": None,  # Invoice オブジェクト
                        "text": "",
                        "bytes": f.read(),
                    }
                )

    # ② 実行ボタン
    with mid:
        st.subheader("② 実行")
        has_files = len(st.session_state.pdf_files) > 0
        run_btn = st.button(
            "OCR→Excelテンプレートに一括反映",
            type="primary",
            use_container_width=True,
            disabled=not has_files,
        )

        if run_btn and has_files:
            _run_ocr_and_fill_excel(ocr_service, excel_service)

    # ③ 結果プレビュー・ダウンロード
    with right:
        st.subheader("③ 結果プレビュー・ダウンロード")
        _render_results_area()

    st.divider()
    st.caption(
        "テンプレはプロジェクト直下の `template_output.xlsx` を使用します（必須）。"
        "セル位置は config.json の `excel_cell_map` で調整できます。"
    )


def _run_ocr_and_fill_excel(
    ocr_service: OcrService,
    excel_service: ExcelService,
) -> None:
    invoices: List[Invoice] = []

    for idx, file_info in enumerate(st.session_state.pdf_files):
        st.session_state.pdf_files[idx]["status"] = "処理中"
        with st.spinner(f"🔄 {file_info['name']} をOCR実行中…"):
            try:
                invoice = ocr_service.analyze_invoice(file_info["bytes"])
                st.session_state.pdf_files[idx]["status"] = "完了"
                st.session_state.pdf_files[idx]["invoice"] = invoice
                st.session_state.pdf_files[idx]["text"] = invoice.raw_text or ""
                invoices.append(invoice)
                st.success(f"✅ {file_info['name']} の処理が完了しました")
            except Exception as e:
                st.session_state.pdf_files[idx]["status"] = "エラー"
                st.error(
                    f"❌ {file_info['name']} の処理中にエラーが発生しました: {str(e)}"
                )

    # まとめて Excel に書き込み
    excel_path = excel_service.write_invoices(invoices)
    st.session_state.output_file = excel_path


def _render_results_area() -> None:
    # Excel ダウンロードボタン
    output_path = st.session_state.get("output_file") or ""
    if output_path and Path(output_path).exists():
        with open(output_path, "rb") as f:
            st.download_button(
                label="まとめてExcelダウンロード",
                data=f.read(),
                file_name="output_combined.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            )

    # PDF ごとの OCR テキストプレビュー
    if st.session_state.pdf_files:
        for file_info in st.session_state.pdf_files:
            st.write(f"**{file_info['name']}** - {file_info['status']}")
            if file_info["status"] == "完了":
                st.text_area(
                    "OCRテキスト",
                    file_info["text"],
                    height=150,
                    key=f"text_{file_info['name']}",
                )
            elif file_info["status"] == "エラー":
                st.write("エラーが発生しました。")
