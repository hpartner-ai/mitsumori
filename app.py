import streamlit as st

from estimate_proto.config import load_app_config, init_env
from estimate_proto.ui.main_page import render_main_page


def main() -> None:
    """
    Streamlit アプリのエントリポイント。
    - .env の読み込み
    - config.json の読み込み
    - メインページ描画
    """
    init_env()
    cfg = load_app_config()

    st.set_page_config(
        page_title="見積プロトタイプ（PDF→テンプレ）",
        layout="wide",
    )

    render_main_page(cfg)


if __name__ == "__main__":
    main()
