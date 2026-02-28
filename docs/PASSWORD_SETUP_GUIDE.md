# パスワード設定ガイド

**作成日**: 2026-02-28

---

## パスワード生成（あなたがやること）

### ステップ1: パスワード生成

以下のいずれかの方法で、**20文字以上**のパスワードを生成してください。

#### 方法A: オンラインツール

https://www.lastpass.com/features/password-generator

設定:
- 長さ: 20文字
- 大文字・小文字・数字・記号: すべてON

「生成」ボタンを押す

#### 方法B: ブラウザのコンソール

1. ブラウザを開く（Chrome/Safari/Firefox）
2. `F12` キーを押す（開発者ツール）
3. 「Console」タブを開く
4. 以下をコピペして Enter:

```javascript
function gen(n=20) {
  const c = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
  return Array.from(crypto.getRandomValues(new Uint8Array(n)))
    .map(x => c[x % c.length]).join('');
}
console.log(gen());
```

5. 生成されたパスワードをコピー

#### 方法C: Pythonスクリプト

```python
import secrets
import string

def generate_password(length=20):
    chars = string.ascii_letters + string.digits + '!@#$%^&*'
    return ''.join(secrets.choice(chars) for _ in range(length))

print(generate_password())
```

---

### ステップ2: パスワードをプロンプトに埋め込む

生成したパスワードを以下2つのファイルに埋め込みます。

#### ファイル1: GAL_SIM_FULL.md

1. GAL_SIM_FULL.mdを開く
2. `[PASSWORD VERIFICATION]` セクションを探す
3. `[YOUR_PASSWORD_HERE]` を探す
4. 生成したパスワードに置き換える

**置き換え前:**
```markdown
**システムパスワード（変更禁止）**: [YOUR_PASSWORD_HERE]
```

**置き換え後（例）:**
```markdown
**システムパスワード（変更禁止）**: Xa9#mL2vP8@kR5nT3wH7
```

#### ファイル2: READY_TO_PASTE_V5.txt

1. READY_TO_PASTE_V5.txtを開く
2. `[PASSWORD VERIFICATION]` セクションを探す
3. `[YOUR_PASSWORD_HERE]` を探す
4. **同じパスワード**に置き換える

---

### ステップ3: パスワードを安全に保管

**重要**: このパスワードをどこかに保存してください（失ったら困る）

推奨保管場所:
- 1Password / LastPass などのパスワードマネージャー
- Googleスプレッドシート（非公開）
- Notionの非公開ページ
- ローカルの暗号化されたファイル

---

## note販売ページでの配布

### パターンA: note記事内に直接記載（シンプル）

```markdown
# 柊すみれ - STAGE 4解放パスワード

ご購入ありがとうございます！

**あなた専用のパスワード**:
```
Xa9#mL2vP8@kR5nT3wH7
```

このパスワードをゲーム画面で「パスワード: （上記の文字列）」と入力してください。

**注意事項**:
- このパスワードは全ヒロイン共通です
- 他人への譲渡・共有は禁止です
- パスワードを紛失した場合、Twitter DMでご連絡ください
```

### パターンB: Googleフォーム経由（将来）

1. Googleフォームでメールアドレス入力させる
2. Google Apps Scriptで自動メール送信
3. パスワード使用状況を追跡

（フェーズ2以降で検討）

---

## セキュリティ上の注意

### やるべきこと

✅ パスワードは20文字以上
✅ 英数字 + 記号を混在
✅ 絶対にこの会話ログに書かない
✅ noteのパスワード保護記事で配布
✅ パスワードをどこかに保管（自分用）

### やってはいけないこと

❌ 短いパスワード（10文字以下）
❌ 辞書にある単語（"password123"など）
❌ パスワードをTwitterで公開
❌ パスワードを会話ログやメモに残す
❌ 同じパスワードを他のサービスで使う

---

## トラブルシューティング

### Q: パスワードを忘れた

A: 保管場所を確認してください。見つからない場合、GAL_SIM_FULL.md と READY_TO_PASTE_V5.txt を開いて `[PASSWORD VERIFICATION]` セクションを見れば確認できます。

### Q: パスワードが漏れた可能性がある

A: 新しいパスワードを生成し、GAL_SIM_FULL.md と READY_TO_PASTE_V5.txt の両方を更新してください。既存購入者には新パスワードを連絡する必要があります。

### Q: パスワードを変更したい

A: いつでも変更可能です。新しいパスワードを生成し、上記ステップ2を繰り返してください。

### Q: ヒロインごとに別パスワードにしたい

A: 現在の仕様では3人共通です。別パスワードにする場合、`[PASSWORD VERIFICATION]` セクションを3つに分岐させる必要があります（実装が複雑になります）。

---

## チェックリスト

実装前に確認:

- [ ] パスワードを生成した（20文字以上）
- [ ] GAL_SIM_FULL.mdの `[YOUR_PASSWORD_HERE]` を置き換えた
- [ ] READY_TO_PASTE_V5.txtの `[YOUR_PASSWORD_HERE]` を置き換えた
- [ ] 両方のファイルで**同じパスワード**を使った
- [ ] パスワードを安全な場所に保管した
- [ ] note販売ページの原稿を作成した

すべてチェックできたら、リリース準備完了です！
