# back/ — 旧プロンプトファイル退避フォルダ

## 退避日
2026-03-01

## 退避理由

海外展開（itch.io / Patreon）に向けたアーキテクチャ刷新のため、旧ファイルを退避。

### 旧アーキテクチャの問題点
- 各キャラFULL.mdにGMルール（ゲーム進行ロジック）とキャラデータが混在していた
- 日本語のみ縛りがFULL.md内に埋め込まれており、多言語対応が困難
- 無料版ゲートのメッセージ（note/¥）が全ファイルにハードコードされており、プラットフォーム別対応ができなかった

### 新アーキテクチャ（予定）

```
prompts/
├── GEM_INSTRUCTIONS_JP.md    ← 日本向けGMルール（note、日本語のみ、¥）
├── GEM_INSTRUCTIONS_EN.md    ← 海外向けGMルール（itch.io/Patreon、多言語、$）
│
├── characters/               ← キャラデータのみ（地域共通）
│   ├── SAKURAI_HIKARI.md
│   ├── SUMIRE.md
│   ├── AYA.md
│   └── HINATA.md
│
└── back/                     ← このフォルダ（旧ファイル）
```

ユーザーは「GEM_INSTRUCTIONS_JP or EN」+「キャラMD」の2ファイルをGeminiに貼る。

## ファイル一覧

| ファイル | 内容 | 状態 |
|---------|------|------|
| GEM_INSTRUCTIONS.md | GMルール（日本向け最新版） | 参照元として保持 |
| SAKURAI_HIKARI_FULL.md | 桜井ひかり（GMルール混在版） | 参照元として保持 |
| SUMIRE_FULL.md | 柊すみれ（GMルール混在版） | 参照元として保持 |
| AYA_FULL.md | 水瀬亜矢（GMルール混在版） | 参照元として保持 |
| HINATA_FULL.md | 星野ひなた（GMルール混在版） | 参照元として保持 |
