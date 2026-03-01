#!/usr/bin/env python3
"""
GAL_SIM ヒロイン キャラクターMD ビルドツール

使い方:
  python tools/build_heroine.py [yaml_path]

yaml_path を省略すると galge-heroines/ の最新ファイルを自動選択。

出力:
  prompts/characters/<filename>.md  （SAKURAI_HIKARI.md 形式）
"""

import json
import os
import re
import secrets
import string
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
EXPAND_PROMPT_PATH = Path(__file__).parent / "gal_sim_expand.md"
OUTPUT_DIR = ROOT / "prompts" / "characters"
GALGE_HEROINES_DIR = Path(
    "/Users/kenjihachiya/Desktop/work/development/character/output/galge-heroines"
)


def generate_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def find_yaml(yaml_path_arg: str | None) -> Path:
    if yaml_path_arg:
        path = Path(yaml_path_arg)
        if not path.exists():
            raise FileNotFoundError(f"YAMLファイルが見つかりません: {path}")
        return path

    if not GALGE_HEROINES_DIR.exists():
        raise FileNotFoundError(f"galge-heroinesディレクトリが見つかりません: {GALGE_HEROINES_DIR}")

    yamls = sorted(
        GALGE_HEROINES_DIR.glob("*.yaml"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not yamls:
        raise FileNotFoundError(f"galge-heroinesにYAMLがありません: {GALGE_HEROINES_DIR}")

    print(f"最新ファイル使用: {yamls[0].name}")
    return yamls[0]


def call_claude(prompt: str) -> str:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=600,
            env=env,
        )
    except FileNotFoundError:
        raise RuntimeError("claude コマンドが見つかりません")
    except subprocess.TimeoutExpired:
        raise RuntimeError("タイムアウト（300秒）。再試行してください")

    if result.returncode != 0:
        raise RuntimeError(f"claude CLI失敗:\n{result.stderr}")

    return result.stdout


def _extract_last_fenced_block(response: str, lang: str) -> str | None:
    """```lang ... ``` ブロックを抽出する。
    内部に入れ子の``` フェンスがある場合でも、
    レスポンス末尾に最も近い``` を外側クローズとして扱う。
    """
    start_marker = f"```{lang}"
    start = response.find(start_marker)
    if start == -1:
        return None
    content_start = response.find("\n", start)
    if content_start == -1:
        return None
    content_start += 1  # \n の次

    # 末尾から逆検索して外側クローズフェンスを探す
    last_fence = response.rfind("\n```")
    if last_fence == -1 or last_fence < content_start:
        return None

    return response[content_start:last_fence].strip()


def parse_response(response: str) -> tuple[dict, str]:
    """レスポンスからJSON（vars）とmarkdown（character section）を抽出"""

    # JSON抽出
    json_match = re.search(r"```json\s*(.*?)```", response, re.DOTALL)
    if not json_match:
        raise ValueError("JSONブロックが見つかりません\n--- response head ---\n" + response[:500])
    vars_dict = json.loads(json_match.group(1))

    # markdownセクション抽出
    # NOTE: re.DOTALL + 非貪欲(.*?)だとCHINK-Aなどの内部コードフェンス```で止まるため、
    # rfindで最後の```を外側クローズとして扱う方式に変更
    character_section = _extract_last_fenced_block(response, "markdown")
    if character_section is None:
        character_section = _extract_last_fenced_block(response, "md")
    if character_section is None:
        raise ValueError("markdownブロックが見つかりません\n--- response head ---\n" + response[:500])
    return vars_dict, character_section


def build_character_md(vars_dict: dict, character_section: str) -> str:
    """SAKURAI_HIKARI.md 形式のキャラクターMDを生成"""
    if "PASSWORD" not in vars_dict or not vars_dict["PASSWORD"]:
        vars_dict["PASSWORD"] = generate_password()

    # Claudeが # キャラクター知識ファイル： ヘッダーを含めて出力した場合はそのまま使う
    if character_section.startswith("# キャラクター知識ファイル："):
        return character_section + "\n"

    # 旧形式（## 組み込みヒロイン：）の場合はヘッダーを付与して変換
    full_name = vars_dict.get("FULL_NAME", "不明")

    furigana = ""
    m = re.search(r"## 組み込みヒロイン：.+?（(.+?)）", character_section)
    if m:
        furigana = m.group(1)

    name_with_furigana = f"{full_name}（{furigana}）" if furigana else full_name

    header = (
        f"# キャラクター知識ファイル：{name_with_furigana}\n"
        "\n"
        "> **使い方**: GEM_INSTRUCTIONS_JP.md または GEM_INSTRUCTIONS_EN.md と一緒にGeminiに貼り付けて使う。\n"
    )

    body = re.sub(
        r"^---\s*\n+## 組み込みヒロイン：.+",
        "## ヒロインプロフィール",
        character_section,
        count=1,
        flags=re.MULTILINE,
    )

    return header + "\n" + body + "\n"


def derive_output_name(yaml_path: Path) -> str:
    stem = yaml_path.stem  # e.g., "01_sakurai_hikari" or "sakurai_hikari"
    stem = re.sub(r"^\d+_", "", stem)  # 数字プレフィックス除去
    return stem.upper() + ".md"


def main():
    yaml_arg = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        yaml_path = find_yaml(yaml_arg)
    except FileNotFoundError as e:
        print(f"エラー: {e}")
        sys.exit(1)

    yaml_text = yaml_path.read_text(encoding="utf-8")
    expand_prompt = EXPAND_PROMPT_PATH.read_text(encoding="utf-8")

    full_prompt = (
        expand_prompt
        + "\n\n---\n\n## 入力キャラクターYAML\n\n```yaml\n"
        + yaml_text
        + "\n```"
    )

    print(f"処理中: {yaml_path.name}")
    print("Claude に拡張データを生成させています（最大5分）...")

    try:
        response = call_claude(full_prompt)
    except RuntimeError as e:
        print(f"Claude呼び出しエラー: {e}")
        sys.exit(1)

    try:
        vars_dict, character_section = parse_response(response)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"パースエラー: {e}")
        sys.exit(1)

    result = build_character_md(vars_dict, character_section)

    out_name = derive_output_name(yaml_path)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / out_name
    out_path.write_text(result, encoding="utf-8")

    print(f"\n✅ 生成完了: {out_path.relative_to(ROOT)}")
    print(f"   ヒロイン: {vars_dict.get('FULL_NAME', '?')}")
    print(f"   モード:   {vars_dict.get('MODE_NAME', '?')}")
    print(f"   CHINK:   {vars_dict.get('CHINK_SUMMARY', '?')}")
    print(f"   PASSWORD: {vars_dict.get('PASSWORD', '?')}")
    print(f"   行数:     {len(result.splitlines())}")


if __name__ == "__main__":
    main()
