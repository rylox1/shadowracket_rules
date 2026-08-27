#!/usr/bin/env python3
"""下载并将 Shadowrocket 模块转换为 RULE-SET 规则集。"""

from __future__ import annotations

import os
import re
import tempfile
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "direct": "https://raw.githubusercontent.com/GMOogway/shadowrocket-rules/master/sr_direct_list.module",
    "proxy": "https://raw.githubusercontent.com/GMOogway/shadowrocket-rules/master/sr_proxy_list.module",
    "reject": "https://raw.githubusercontent.com/GMOogway/shadowrocket-rules/master/sr_reject_list.module",
}
MIN_RULES = {
    "direct": 1_000,
    "proxy": 100,
    "reject": 1_000,
}
RULE_LINE = re.compile(r"^[A-Z][A-Z-]*,")
POLICY_AT_END = re.compile(
    r",(?P<policy>DIRECT|PROXY|REJECT(?:-[A-Z0-9-]+)?)(?P<options>(?:,[^,\s]+)*)\s*$"
)


def fetch(url: str) -> str:
    """下载远程模块内容。

    Args:
        url: 模块地址。

    Returns:
        模块的 UTF-8 文本。

    Raises:
        OSError: 网络请求失败或响应状态异常。
        UnicodeError: 响应不是有效的 UTF-8 文本。
    """
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "shadowracket-rules-builder/1.0"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        status = getattr(response, "status", 200)
        if status != 200:
            raise OSError(f"下载失败: HTTP {status}: {url}")
        return response.read().decode("utf-8-sig")


def convert_module(content: str, name: str) -> list[str]:
    """提取模块的规则并删除策略列。

    Args:
        content: Shadowrocket 模块文本。
        name: 规则集名称,用于错误信息。

    Returns:
        符合 RULE-SET 格式的去重规则行。

    Raises:
        ValueError: 模块缺少规则段或存在无法识别的规则行。
    """
    in_rule_section = False
    output: list[str] = []
    seen: set[str] = set()

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if line.lower() == "[rule]":
            in_rule_section = True
            continue
        if line.startswith("[") and line.endswith("]"):
            in_rule_section = False
            continue
        if not in_rule_section or not line or line.startswith("#"):
            continue
        if not RULE_LINE.match(line):
            continue

        match = POLICY_AT_END.search(line)
        if match is None:
            raise ValueError(f"{name}: 无法识别规则策略: {line}")

        # 保留 no-resolve、extended-matching 等选项,只删除策略本身。
        normalized = line[: match.start()] + match.group("options")
        if normalized not in seen:
            seen.add(normalized)
            output.append(normalized)

    if not output:
        raise ValueError(f"{name}: 未找到任何规则")
    return output


def render(name: str, source: str, rules: list[str]) -> str:
    """生成规则集文件文本。"""
    header = [
        "# Shadowrocket RULE-SET,由 GitHub Actions 自动生成",
        f"# 来源: {source}",
        f"# 规则数: {len(rules)}",
        "",
    ]
    return "\n".join(header + rules) + "\n"


def build() -> None:
    """下载、校验并原子更新三个规则集文件。"""
    generated: dict[str, str] = {}
    for name, url in SOURCES.items():
        content = fetch(url)
        rules = convert_module(content, name)
        minimum = MIN_RULES[name]
        if len(rules) < minimum:
            raise ValueError(
                f"{name}: 规则数异常,得到 {len(rules)} 条,期望至少 {minimum} 条"
            )
        generated[f"{name}.list"] = render(name, url, rules)
        print(f"{name}: {len(rules)} 条")

    # 全部源文件通过校验后才替换目标文件,避免单个源失败造成空文件。
    with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
        temp_root = Path(temp_dir)
        for filename, content in generated.items():
            temporary = temp_root / filename
            temporary.write_text(content, encoding="utf-8")
            os.replace(temporary, ROOT / filename)


if __name__ == "__main__":
    build()
