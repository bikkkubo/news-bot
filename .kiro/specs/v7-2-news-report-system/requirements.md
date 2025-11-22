# Requirements Document

## Introduction

V7.2 ニュースレポート自動生成システムは、Slack からのトリガーにより、信頼できる金融ニュースソースから最新情報を収集・分析し、YouTube 動画コンテンツ作成とリサーチ用の高品質な日本語レポートを自動生成するシステムです。

本システムは、複数のデータソース（NewsAPI.org、RSS フィード、LLM）を組み合わせ、実在する URL のみを使用した透明性の高いレポートを生成します。また、レポートと同時に動画用の字幕・台本も自動生成します。

## Requirements

### Requirement 1: Slack トリガーによるレポート生成

**User Story:** Slack ユーザーとして、特定のチャンネルで bot にメンションすることで、最新の金融ニュースレポートを自動生成したい。これにより、必要なタイミングで最新情報を入手できる。

#### Acceptance Criteria

1. WHEN ユーザーがチャンネル ID `C09S2KBK3HU` で `@news_bot` にメンションを送信 THEN システムは目のスタンプ（:eyes:）で反応を返す SHALL
2. WHEN システムがメンションを受信 THEN システムはスレッド内に処理開始メッセージを投稿する SHALL
3. WHEN システムが処理を開始 THEN システムは各ステップの進捗状況をスレッドに投稿する SHALL
4. WHEN システムがレポート生成を完了 THEN システムは完了メッセージとチェックマークスタンプ（:white_check_mark:）を投稿する SHALL
5. WHEN システムがエラーに遭遇 THEN システムはエラーメッセージと X スタンプ（:x:）を投稿する SHALL
6. IF メンションが対象チャンネル以外から送信された場合 THEN システムは反応しない SHALL

### Requirement 2: 株価データの取得と表示

**User Story:** レポート読者として、主要株価指数の最新データを確認したい。これにより、市場全体の動向を把握できる。

#### Acceptance Criteria

1. WHEN システムが株価データ取得を開始 THEN システムは yfinance ライブラリを使用して以下の指数データを取得する SHALL
   - ダウ平均（^DJI）
   - ナスダック（^IXIC）
   - S&P 500（^GSPC）
   - 日経 225（^N225）
2. WHEN 各指数のデータを取得 THEN システムは終値、前日比、前日比（%）を記録する SHALL
3. IF 特定の指数のデータ取得に失敗した場合 THEN システムは警告をログに記録し、他の指数の取得を続行する SHALL
4. WHEN すべての株価データ取得が完了 THEN システムはデータをレポートの「市場全体の動向」セクションに含める SHALL

### Requirement 3: 信頼できるニュースソースからのデータ収集

**User Story:** レポート作成者として、信頼できるニュースソースから最新情報を収集したい。これにより、正確で信頼性の高いレポートを生成できる。

#### Acceptance Criteria

1. WHEN システムがニュースデータ収集を開始 THEN システムは以下のソースから情報を取得する SHALL
   - NewsAPI.org（Bloomberg、WSJ、Reuters - 日米両方）
   - Investing.com RSS フィード（米国版・日本版）
2. WHEN NewsAPI.org からデータを取得 THEN システムは `/top-headlines` エンドポイントを使用し、以下のソースを指定する SHALL
   - Bloomberg（米国版・日本版）
   - The Wall Street Journal（米国版・日本版）
   - Reuters（米国版・日本版）
3. WHEN Investing.com からデータを取得 THEN システムは過去 24 時間以内の記事のみを収集する SHALL
4. IF NewsAPI.org からのデータ取得に失敗した場合 THEN システムは警告をログに記録し、RSS フィードのデータのみで処理を続行する SHALL
5. IF RSS フィードからのデータ取得に失敗した場合 THEN システムは警告をログに記録し、NewsAPI.org のデータのみで処理を続行する SHALL
6. WHEN 重複する記事タイトルが検出された場合 THEN システムは重複を削除し、最初の記事のみを保持する SHALL

### Requirement 4: LLM による初期ニュース生成

**User Story:** システム管理者として、LLM の内部知識を活用して直近 12 時間以内の重要ニュースの草案を生成したい。これにより、最新の市場動向を網羅的に把握できる。

#### Acceptance Criteria

1. WHEN システムが初期ニュース生成を開始 THEN システムは以下の優先順位で LLM モデルを選択する SHALL
   - 第 1 優先: Google Gemini 3.0（`GOOGLE_API_KEY`が設定されている場合）
   - 第 2 優先: OpenAI GPT-5.1（Gemini 3.0 が利用できず、`OPENAI_API_KEY`が設定されている場合）
   - 第 3 優先: Anthropic Claude 3.5 Sonnet（上記 2 つが利用できず、`ANTHROPIC_API_KEY`が設定されている場合）
2. IF すべての LLM API キーが設定されていない場合 THEN システムはエラーメッセージを表示し、処理を中止する SHALL
3. WHEN LLM にプロンプトを送信 THEN システムは以下の条件を指定する SHALL
   - 直近 12 時間以内のニュース
   - 15 件のニュース生成
   - セクター別配分（テクノロジー 4-5 件、マクロ経済 3-4 件、金融 2-3 件、エネルギー 2-3 件、その他 2-3 件）
   - 地域別配分（米国 10-12 件、日本 3-5 件）
   - ソース別配分（Bloomberg、Reuters、WSJ、CNBC、MarketWatch から均等に）
4. WHEN LLM がニュースを生成 THEN 各ニュースは以下の情報を含む SHALL
   - タイトル（日本語、具体的な数字を含む）
   - URL（"N/A"と設定）
   - 発表時刻（YYYY-MM-DD HH:MM:SS 形式）
   - ソース名
   - 概要（100-200 文字）
   - セクター
   - 地域
   - 重要度
   - キーワード
   - 市場への影響
   - 関連銘柄
5. IF 生成されたニュースが 15 件未満の場合 THEN システムは警告をログと Slack スレッドに投稿し、処理を続行する SHALL

### Requirement 5: 補助データを参考にした深堀り分析

**User Story:** レポート読者として、初期ニュースに実際の URL と詳細な分析を追加したい。これにより、情報の信頼性と有用性が向上する。

#### Acceptance Criteria

1. WHEN システムが深堀り分析を開始 THEN システムは初期ニュース、補助データ（NewsAPI.org、Investing.com）、株価データを LLM に提供する SHALL
2. WHEN LLM が深堀り分析を実行 THEN システムは以下の指示を含める SHALL
   - 補助データから関連情報を抽出
   - 具体的な数字、銘柄名、影響を追加
   - 各文節に補助データの実際の URL のみを配置
   - 架空の URL は絶対に作成しない
3. WHEN 深堀り分析が完了 THEN 各ニュースは以下の情報を含む SHALL
   - 企業情報（企業名、ティッカー、時価総額、セクター）
   - 詳細な概要（各文節にソース URL を配置）
   - 市場への影響（プラス/マイナスの理由、懸念事項、影響を受けるセクター/銘柄、短期・長期の影響）
   - 投資家への示唆
   - 補助データの実際の URL
4. WHEN システムが URL を検証 THEN システムは以下のドメインの URL のみを許可する SHALL
   - investing.com
   - bloomberg.com
   - wsj.com
   - reuters.com
5. IF 架空の URL が検出された場合 THEN システムはその URL を削除し、警告をログに記録する SHALL

### Requirement 6: V7.1 形式のレポート生成

**User Story:** レポート読者として、市場動向分析と個別ニュース解説を含む包括的な Markdown レポートを受け取りたい。これにより、市場全体を理解し、個別ニュースの詳細を確認できる。

#### Acceptance Criteria

1. WHEN システムがレポート生成を開始 THEN システムは以下のセクションを含む Markdown ファイルを作成する SHALL
   - タイトルと発行日
   - 市場全体の動向（米国市場、日本市場、市場動向分析）
   - ピックアップニュース（15 件以上）
2. WHEN 市場動向分析を生成 THEN システムは LLM を使用して以下の内容を含める SHALL
   - 米国市場の動向（主要 3 指数の変動、前日比較、セクター別の動き、市場心理）
   - 日本市場の動向（日経 225 の変動、前日比較、米国市場との連動性、為替の影響）
   - 市場全体のトレンド（共通点、注目ポイント、今後の見通し）
3. WHEN 個別ニュースをレポートに追加 THEN 各ニュースは以下の構造を持つ SHALL
   - タイトル
   - 企業情報
   - ニュース概要（ソース URL を含む）
   - 市場への影響（深堀り）
   - 投資家への示唆
   - 出典
4. WHEN レポートが完成 THEN システムはファイル名を `YYYYMMDD_ニュースまとめ_v7_2_hybrid.md` とする SHALL

### Requirement 7: 動画用字幕と台本の自動生成

**User Story:** 動画作成者として、レポートを元にした字幕と台本を自動生成したい。これにより、YouTube 動画コンテンツを効率的に作成できる。

#### Acceptance Criteria

1. WHEN システムがレポート生成を完了 THEN システムは自動的に動画用字幕と台本の生成を開始する SHALL
2. WHEN 字幕を生成 THEN システムは LLM を使用してレポート内容を以下の形式に変換する SHALL
   - 「です・ます」調
   - 1 行あたり適切な長さ（読みやすさを考慮）
   - 具体的な数字を保持
3. WHEN 台本を生成 THEN システムは以下の内容を含める SHALL
   - オープニング（挨拶、日付、概要）
   - 市場全体の動向（主要指数の変動）
   - 個別ニュース（タイトル、概要、市場への影響、投資家への示唆）
   - クロージング（まとめ、挨拶）
4. WHEN 字幕と台本が完成 THEN システムは以下のファイルを生成する SHALL
   - `YYYYMMDD_動画用字幕.txt`
   - `YYYYMMDD_ニュース台本.txt`
   - `YYYYMMDD_動画用素材取得用リンク.md`
5. WHEN 動画用素材リンクを生成 THEN システムは各ニュースに関連する画像 URL をリスト化する SHALL

### Requirement 8: 出力ファイルの Slack へのアップロード

**User Story:** Slack ユーザーとして、生成されたすべてのファイルをスレッド内で受け取りたい。これにより、ファイルに簡単にアクセスでき、ローカルファイルの管理が不要になる。

#### Acceptance Criteria

1. WHEN すべてのファイル生成が完了 THEN システムは以下のファイルを Slack スレッドにアップロードする SHALL
   - ニュースまとめ（.md）
   - ニュースデータ（.json）
   - 実行ログ（.txt）
   - 動画用字幕（.txt）
   - ニュース台本（.txt）
   - 動画用素材取得用リンク（.md）
2. WHEN 各ファイルをアップロード THEN システムは適切な説明コメントを添付する SHALL
3. IF ファイルが存在しない場合 THEN システムはそのファイルをスキップし、警告をログに記録する SHALL
4. WHEN ファイルが Slack にアップロードされた後 THEN システムはローカルファイルを保持する SHALL（自動削除は行わない）
5. WHEN すべてのファイルがアップロードされた THEN ユーザーは Slack から直接ファイルをダウンロードできる SHALL

### Requirement 9: エラーハンドリングとロギング

**User Story:** システム管理者として、エラーが発生した場合でも適切に処理され、詳細なログが記録されることを確認したい。これにより、問題の診断と解決が容易になる。

#### Acceptance Criteria

1. WHEN システムがエラーに遭遇 THEN システムはエラーメッセージを Slack スレッドに投稿する SHALL
2. WHEN エラーが発生 THEN システムはエラーの詳細（スタックトレース、タイムスタンプ）を実行ログに記録する SHALL
3. WHEN 各ステップが完了 THEN システムは実行時間と成功/失敗ステータスをログに記録する SHALL
4. WHEN 実行ログが完成 THEN システムはファイル名を `YYYYMMDD_execution_log_v7_2_hybrid.txt` とする SHALL
5. IF 一部のデータソースが利用できない場合 THEN システムは警告を記録し、利用可能なデータで処理を続行する SHALL

### Requirement 10: 環境変数とセキュリティ

**User Story:** システム管理者として、API キーやトークンを安全に管理したい。これにより、セキュリティリスクを最小限に抑えられる。

#### Acceptance Criteria

1. WHEN システムが起動 THEN システムは `.env` ファイルから以下の環境変数を読み込む SHALL
   - LLM API キー（`GOOGLE_API_KEY`、`OPENAI_API_KEY`、または `ANTHROPIC_API_KEY` のいずれか）
   - `NEWSAPI_KEY`
   - `SLACK_BOT_TOKEN`
   - `SLACK_APP_TOKEN`
   - `SLACK_CHANNEL_ID`（デフォルト値: C09S2KBK3HU）
2. IF 必須の環境変数が設定されていない場合 THEN システムはエラーメッセージを表示し、起動を中止する SHALL
3. WHEN API キーを使用 THEN システムはキーをログや Slack メッセージに出力しない SHALL
