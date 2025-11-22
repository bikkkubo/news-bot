# APIキー・設定値の取得方法

このシステムを動作させるために必要な各サービスのAPIキーや設定値の取得手順です。

## 1. LLM API Keys (いずれか1つ以上必須)

### Google Gemini (`GOOGLE_API_KEY`)
1. [Google AI Studio](https://aistudio.google.com/) にアクセスし、Googleアカウントでログインします。
2. 左側のメニューから **"Get API key"** をクリックします。
3. **"Create API key"** をクリックし、新しいプロジェクトまたは既存のプロジェクトを選択してキーを作成します。
4. 表示されたキーをコピーします。

### OpenAI (`OPENAI_API_KEY`)
1. [OpenAI Platform](https://platform.openai.com/api-keys) にアクセスし、アカウントでログインします。
2. **"Create new secret key"** をクリックします。
3. 名前（例: "News Bot"）を入力し、キーを作成します。
4. 表示されたキーをコピーします（一度しか表示されないので注意してください）。

### Anthropic Claude (`ANTHROPIC_API_KEY`)
1. [Anthropic Console](https://console.anthropic.com/settings/keys) にアクセスし、アカウントでログインします。
2. **"Create Key"** をクリックします。
3. 名前を入力し、キーを作成します。
4. 表示されたキーをコピーします。

---

## 2. News API (`NEWSAPI_KEY`)

1. [NewsAPI.org](https://newsapi.org/) にアクセスし、**"Get API Key"** をクリックします。
2. アカウント登録（無料）を行います。
3. 登録完了後、ダッシュボードに表示される API Key をコピーします。

---

## 3. Slack 設定

### Bot Token & App Token
1. [Slack API: Your Apps](https://api.slack.com/apps) にアクセスし、**"Create New App"** をクリックします。
2. **"From scratch"** を選択し、アプリ名（例: "News Bot"）とワークスペースを選択して **"Create App"** をクリックします。
3. **Socket Mode の有効化**:
   - 左メニュー **"Socket Mode"** を選択し、**"Enable Socket Mode"** をオンにします。
   - トークン名を入力し、生成された `xapp-` から始まるトークンをコピーします (**`SLACK_APP_TOKEN`**)。
4. **権限の設定**:
   - 左メニュー **"OAuth & Permissions"** を選択します。
   - **"Scopes"** > **"Bot Token Scopes"** に以下の権限を追加します：
     - `app_mentions:read` (メンションの読み取り)
     - `chat:write` (メッセージの投稿)
     - `files:write` (ファイルのアップロード)
     - `reactions:write` (リアクションの追加)
5. **アプリのインストール**:
   - 同ページ上部の **"Install to Workspace"** をクリックし、許可します。
   - 表示された `xoxb-` から始まるトークンをコピーします (**`SLACK_BOT_TOKEN`**)。
6. **イベント購読の設定**:
   - 左メニュー **"Event Subscriptions"** を選択し、オンにします。
   - **"Subscribe to bot events"** で `app_mention` を追加し、保存します。

### Channel ID (`SLACK_CHANNEL_ID`)
1. Slack アプリを開き、Bot を動かしたいチャンネルを右クリックします。
2. **"リンクをコピー"** を選択します。
3. リンクの末尾の `C` から始まる文字列（例: `.../archives/C09S2KBK3HU` の `C09S2KBK3HU`）がチャンネルIDです。
4. **重要**: そのチャンネルに作成したアプリ（Bot）を招待してください（チャンネルで `@Bot名` と入力して招待）。

---

## 4. Google Drive 設定 (任意)

### サービスアカウントキー (`GOOGLE_SERVICE_ACCOUNT_JSON`)
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセスし、プロジェクトを作成します。
2. **"APIとサービス"** > **"ライブラリ"** から **"Google Drive API"** を検索し、有効にします。
3. **"APIとサービス"** > **"認証情報"** > **"認証情報を作成"** > **"サービスアカウント"** を選択します。
4. 名前を入力して作成し、ロールは「編集者」などを選択して完了します。
5. 作成したサービスアカウントをクリックし、**"キー"** タブへ移動します。
6. **"鍵を追加"** > **"新しい鍵を作成"** > **"JSON"** を選択し、作成します。
7. ダウンロードされた JSON ファイルをプロジェクトのルートフォルダに `credentials.json` という名前で配置します。

### フォルダ ID (`GOOGLE_DRIVE_FOLDER_ID`)
1. Google Drive でファイルを保存したいフォルダを開きます。
2. ブラウザのURLバーを確認します。
3. `drive.google.com/drive/folders/` の後ろの文字列（例: `1a2b3c...`）がフォルダIDです。
4. **重要**: そのフォルダに対して、先ほど作成したサービスアカウントのメールアドレス（JSONファイル内の `client_email`）に「編集者」権限で共有設定を行ってください。
