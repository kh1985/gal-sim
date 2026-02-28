#!/usr/bin/env python3
"""
GAL_SIM ヒロイン _FULL.md ビルドツール

使い方:
  python tools/build_heroine.py [yaml_path]

yaml_path を省略すると galge-heroines/ の最新ファイルを自動選択。

出力:
  prompts/<filename>_FULL.md
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
TEMPLATE_SOURCE = ROOT / "prompts" / "SUMIRE_FULL.md"
OUTPUT_DIR = ROOT / "prompts"
GALGE_HEROINES_DIR = Path(
    "/Users/kenjihachiya/Desktop/work/development/character/output/galge-heroines"
)

# SUMIRE_FULL.md内の固有文字列 → テンプレート変数への置換マップ
# 左辺: SUMIRE_FULL.md内の文字列
# 右辺: {KEY} 形式のプレースホルダー（varsで置換）
INLINE_REPLACEMENTS: list[tuple[str, str]] = [
    (
        "すみれのCHINK、防壁パターン、Say/Do Gapに対応",
        "{FIRST_NAME}のCHINK、防壁パターン、Say/Do Gapに対応",
    ),
    ("ヒロイン（柊すみれ）", "ヒロイン（{FULL_NAME}）"),
    ("（友達モードに戻ろうとする）", "（{MODE_NAME}に戻ろうとする）"),
    (
        "すみれのCHINK（昔と違うね、友達じゃダメ？、他の誰かと付き合ったら）",
        "{FIRST_NAME}のCHINK（{CHINK_SUMMARY}）",
    ),
    (
        "すみれの防壁パターン（友達トーク、恋愛回避、弱点突かれた時の強化反応）",
        "{FIRST_NAME}の防壁パターン（{BARRIER_SUMMARY}）",
    ),
    (
        "プレイヤーは**すみれのペルソナを理解して選ぶ**",
        "プレイヤーは**{FIRST_NAME}のペルソナを理解して選ぶ**",
    ),
    (
        "1. 「すみれ、最近雰囲気変わったよね」（CHINK-A近似）",
        "1. {STAGE1_CHOICE_A}",
    ),
    (
        "2. 「久しぶりだね。元気だった？」（友達トーク維持）",
        "2. {STAGE1_CHOICE_B}",
    ),
    (
        "1. 「俺たち、ずっと友達のままでいいよね」（CHINK-B直撃狙い）",
        "1. {STAGE2_CHOICE_A}",
    ),
    (
        "2. 「すみれ、そのワンピース似合ってるよ」（Say/Do Gap指摘）",
        "2. {STAGE2_CHOICE_B}",
    ),
    (
        "1. 「すみれは、誰かいい人いないの？」（CHINK-C狙い）",
        "1. {STAGE3_CHOICE_A}",
    ),
    ("- すみれに刺さらない行動", "- {FIRST_NAME}に刺さらない行動"),
    ("- すみれのペルソナを無視した行動", "- {FIRST_NAME}のペルソナを無視した行動"),
    (
        '   - 抵抗値0→10: 「…っ、何、してた…の…」（茫然）',
        "   - 抵抗値0→10: {RESET_DIALOGUE}",
    ),
    (
        '「友達モード」に戻ろうとする（でも身体は覚えている）',
        '「{MODE_NAME}」に戻ろうとする（でも身体は覚えている）',
    ),
    ("すみれの肩が、震えた。", "{FIRST_NAME}の肩が、震えた。"),
    ("すみれは鞄を肩にかけ、立ち上がった。", "{FIRST_NAME}は鞄を肩にかけ、立ち上がった。"),
    # パスワード（SUMIRE固有値 → 新キャラのパスワード）
    ("rxXnFWZdWYp7", "{PASSWORD}"),
]

# キャラクターセクションの区切りマーカー
CHARACTER_SECTION_MARKER = "\n## 組み込みヒロイン："


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
            timeout=300,
            env=env,
        )
    except FileNotFoundError:
        raise RuntimeError("claude コマンドが見つかりません")
    except subprocess.TimeoutExpired:
        raise RuntimeError("タイムアウト（300秒）。再試行してください")

    if result.returncode != 0:
        raise RuntimeError(f"claude CLI失敗:\n{result.stderr}")

    return result.stdout


def parse_response(response: str) -> tuple[dict, str]:
    """レスポンスからJSON（vars）とmarkdown（character section）を抽出"""

    # JSON抽出
    json_match = re.search(r"```json\s*(.*?)```", response, re.DOTALL)
    if not json_match:
        raise ValueError("JSONブロックが見つかりません\n--- response head ---\n" + response[:500])
    vars_dict = json.loads(json_match.group(1))

    # markdownセクション抽出
    md_match = re.search(r"```markdown\s*(.*?)```", response, re.DOTALL)
    if not md_match:
        md_match = re.search(r"```md\s*(.*?)```", response, re.DOTALL)
    if not md_match:
        raise ValueError("markdownブロックが見つかりません\n--- response head ---\n" + response[:500])

    character_section = md_match.group(1).strip()
    return vars_dict, character_section


def apply_template(vars_dict: dict, character_section: str) -> str:
    """SUMIRE_FULL.mdをベースに新キャラの_FULL.mdを生成"""
    content = TEMPLATE_SOURCE.read_text(encoding="utf-8")

    # PASSWORDが未指定なら自動生成
    if "PASSWORD" not in vars_dict or not vars_dict["PASSWORD"]:
        vars_dict["PASSWORD"] = generate_password()

    # インライン置換（順序依存しないため全件チェック）
    for old, template_str in INLINE_REPLACEMENTS:
        try:
            new = template_str.format(**vars_dict)
        except KeyError as e:
            print(f"  ⚠️  変数不足（スキップ）: {e} → {template_str!r}")
            continue
        if old in content:
            content = content.replace(old, new)
        else:
            print(f"  ⚠️  マーカーが見つかりませんでした（スキップ）: {old!r}")

    # キャラクターセクションの差し替え
    idx = content.find(CHARACTER_SECTION_MARKER)
    if idx == -1:
        raise ValueError(
            f"キャラクターセクションマーカーが見つかりません: {CHARACTER_SECTION_MARKER!r}"
        )

    # マーカー前の `---` ヘッダーも含めて切り取る
    content_head = content[:idx]
    # 末尾の `\n---\n` を除去（character_section側に含まれるため）
    last_sep = content_head.rfind("\n---\n")
    if last_sep != -1 and last_sep > len(content_head) - 10:
        content_head = content_head[:last_sep]

    return content_head + "\n\n" + character_section + "\n"


def derive_output_name(yaml_path: Path) -> str:
    stem = yaml_path.stem  # e.g., "01_sakurai_hikari" or "sakurai_hikari"
    stem = re.sub(r"^\d+_", "", stem)  # 数字プレフィックス除去
    return stem.upper() + "_FULL.md"


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

    try:
        result = apply_template(vars_dict, character_section)
    except ValueError as e:
        print(f"テンプレート適用エラー: {e}")
        sys.exit(1)

    out_name = derive_output_name(yaml_path)
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
