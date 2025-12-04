from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


def extract_month(text: str) -> Optional[int]:
    """
    テキスト中から「○月」を探して、その数字部分を返す。
    例: '2024年2月分ご請求' → 2
    （半角 1〜12 月を想定）
    """
    match = re.search(r"(\d{1,2})月", text)
    if match:
        m = int(match.group(1))
        if 1 <= m <= 12:
            return m
    return None


def extract_kwh_value(text: str) -> str:
    """
    「12345kWh」「12,345 kWh」など、
    kWh がついている数値だけを抽出して返す。
    0kWh の場合は無視する（空文字を返す）。
    返り値はカンマ除去済みの数字文字列。
    """
    match = re.search(r"([\d,]+)\s*kWh", text)
    if not match:
        return ""

    value_str = match.group(1).replace(",", "")
    try:
        if int(value_str) == 0:
            return ""
    except ValueError:
        return ""

    return value_str


@dataclass
class Invoice:
    """
    1枚の請求書を表すドメインオブジェクト。

    fields:
      - "1月値"〜"12月値" だけを使う（法人名・契約電力は一旦扱わない）
    raw_text:
      - Azure OCR から取得したテキスト全体
    """

    fields: Dict[str, str] = field(default_factory=dict)
    raw_text: str = ""

    @classmethod
    def from_text(cls, text: str, cfg: Dict[str, Any]) -> "Invoice":
        """
        OCR済みテキストをもとに Invoice を生成する。

        ロジック：
        - テキストから「○月」を読む（例: 2月）
        - テキストから「kWh が付いている 0 以外の数値」を1つ拾う
        - 読み取った月を -1 シフトしたキーに "○月値" として保存
          - 1月 → 12月値
          - 2月 → 1月値
          - 3月 → 2月値
          - ...
        - 法人名 / 契約電力 は今回は扱わない
        """
        fields: Dict[str, str] = {}

        month = extract_month(text)
        kwh_value = extract_kwh_value(text)

        if month is not None and kwh_value:
            if month == 1:
                mapped_month = 12
            else:
                mapped_month = month - 1

            fields[f"{mapped_month}月値"] = kwh_value

        return cls(fields=fields, raw_text=text)
