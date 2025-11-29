# Claude Agent SDK Prompt Loading Order Investigation

このプロジェクトは、Python版Claude Agent SDKがプロンプトファイルをどの順番で読み込むかを調査するための環境です。

## 🎯 目的

Claude Agent SDKが以下のファイルをどの順番で読み込むかを特定します:
- `CLAUDE.md` (ルートディレクトリ)
- `.claude/system.md`
- `.claude/instructions.md`
- `.claude/commands/*.md`
- その他のプロンプト関連ファイル

## 📁 プロジェクト構成

```
claude-prompt-search/
├── main.py                      # メインスクリプト（プロンプト読み込み順序を調査）
├── requirements.txt             # Python依存関係
├── .env.example                 # 環境変数のサンプル
├── CLAUDE.md                    # テスト用プロンプトファイル
├── .claude/
│   ├── system.md               # システムプロンプト
│   ├── instructions.md         # インストラクション
│   └── commands/
│       └── test.md             # テストコマンド
└── README.md                    # このファイル
```

## 🚀 セットアップ

### 1. 仮想環境の作成（推奨）

```bash
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

これにより `claude-agent-sdk` パッケージがインストールされます。

### 3. 環境変数の設定

APIキーを環境変数として設定します:

```bash
export ANTHROPIC_API_KEY=your_actual_api_key_here
```

または、`.env`ファイルを作成して設定することもできます:

```bash
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

## 🔍 使用方法

### ✅ 推奨: Claudeに直接質問する方法

最も効果的な調査方法は、Claude自身に読み込んだプロンプトファイルを報告させることです：

```bash
python ask_claude.py
```

このスクリプトはClaudeに以下を質問します：
- どのプロンプトファイルが読み込まれたか
- ファイルの読み込み順序
- 各ファイルの内容と優先順位

**結果ファイル**:
- `claude_full_response.txt` - Claudeの完全な回答
- `claude_response.log` - 詳細なログ

### 代替: ファイル読み込みトレース方法

```bash
python main.py
```

**注意**: この方法ではCLI内部のファイル読み込みは捕捉できません。

### 出力の確認

スクリプトを実行すると、以下の2つの場所にログが出力されます:

1. **コンソール出力**: リアルタイムで進捗を確認
2. **`prompt_loading.log`**: 詳細なログファイル

### ログの例

```
2024-11-29 22:30:00 - __main__ - INFO - ================================================================================
2024-11-29 22:30:00 - __main__ - INFO - Starting Claude Agent SDK Prompt Loading Investigation
2024-11-29 22:30:00 - __main__ - INFO - ================================================================================
2024-11-29 22:30:00 - __main__ - INFO - 📄 FILE READ: /path/to/CLAUDE.md
2024-11-29 22:30:00 - __main__ - INFO - 📄 FILE READ: /path/to/.claude/system.md
2024-11-29 22:30:00 - __main__ - INFO - 📄 FILE READ: /path/to/.claude/instructions.md
...
```

## 📊 調査内容

このスクリプトは以下の方法でプロンプトファイルの読み込みを追跡します:

1. **Monkey Patching**: Python組み込みの`open()`関数をラップ
2. **ファイル読み込みの検出**: プロンプト関連ファイルの読み込みを検出
3. **順序の記録**: 読み込まれた順番を時系列で記録
4. **詳細ログ**: すべての読み込み操作を`prompt_loading.log`に保存

### setting_sources の役割

スクリプトは `ClaudeAgentOptions` の `setting_sources=["project"]` を使用しています。これにより:
- プロジェクトルートの `CLAUDE.md` ファイルが読み込まれます
- `.claude/settings.json` の設定が読み込まれます
- `.claude/` ディレクトリ内の他のプロンプトファイルが読み込まれます

`setting_sources` を省略すると、これらのファイルは読み込まれません。

## 🧪 テストファイルの説明

- **CLAUDE.md**: ルートディレクトリのメインプロンプトファイル
- **.claude/system.md**: システムレベルのプロンプト
- **.claude/instructions.md**: 指示・インストラクション
- **.claude/commands/test.md**: スラッシュコマンド用プロンプト

これらのファイルにはそれぞれ識別用のマーカーが含まれており、どのファイルがいつ読み込まれたかを追跡できます。

## 🔧 トラブルシューティング

### Claude Agent SDKが見つからない場合

```bash
# 正しいパッケージをインストール
pip install claude-agent-sdk
```

### APIキーのエラー

- 環境変数 `ANTHROPIC_API_KEY` が正しく設定されているか確認
  ```bash
  echo $ANTHROPIC_API_KEY
  ```
- `.env`ファイルを使用している場合、ファイルが正しく作成されているか確認
- APIキーが有効か確認（Anthropicのダッシュボードで確認）

### ログファイルが作成されない場合

- スクリプトの実行権限を確認
- ディレクトリの書き込み権限を確認

## 📝 カスタマイズ

### 追加のプロンプトファイルをテストする

新しいプロンプトファイルを追加して、その読み込みを追跡できます:

```bash
# 例: .claude/custom.mdを作成
echo "# Custom Prompt" > .claude/custom.md
```

### ログレベルの変更

`main.py`の`logging.basicConfig`セクションを編集:

```python
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    ...
)
```

## 🎯 調査結果サマリー

詳細な調査結果は [FINDINGS.md](FINDINGS.md) を参照してください。

### 主要な発見

1. **CLAUDE.md が最強の優先順位**
   - デフォルト動作をオーバーライド可能
   - "MUST follow them exactly" という強い指示付き

2. **読み込み順序（優先順位順）**
   ```
   1. [最高] Claude Codeコアシステムプロンプト
   2. [高]   CLAUDE.md
   3. [中]   .claude/system.md
   4. [中]   .claude/instructions.md
   5. [低]   .claude/commands/*.md（条件付き）
   ```

3. **setting_sources が重要**
   - `setting_sources=["project"]` を指定しないとプロンプトファイルは読み込まれない
   - 省略した場合、CLAUDE.mdも.claude/も無視される

4. **Claude自身に聞くのが効果的**
   - Pythonのmonkey patchingでは捕捉不可能
   - CLI内部（Node.js/TypeScript）で読み込まれるため
   - Claude自身に質問する方が確実

## 📚 参考資料

- [FINDINGS.md](FINDINGS.md) - 詳細な調査結果レポート
- [ask_claude.py](ask_claude.py) - Claude自身に質問するスクリプト
- [Claude Agent SDK - Python リファレンス](https://code.claude.com/docs/ja/agent-sdk/python)
- [Claude Agent SDK - 概要](https://code.claude.com/docs/ja/agent-sdk/overview)
- [Anthropic API Documentation](https://docs.anthropic.com/)

## 🤝 貢献

調査結果や改善提案は歓迎します！

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

---

**Note**: このプロジェクトは調査・学習目的で作成されています。Claude Agent SDKの実際の動作は、バージョンや設定によって異なる場合があります。