# LINE Bot FAQ Service

このプロジェクトは、LINEメッセージングAPIを使用してFAQサービスを提供するためのLINEボットです。ユーザーが質問を送信すると、ボットは適切な回答を返信します。また、複数の回答候補がある場合は、ボタンテンプレートを使用してユーザーに選択肢を提示します。

## 機能

- テキストメッセージに基づいてFAQの回答を提供します。回答が得られなかった場合は、googleの検索リンクを提供します。
- 回答候補が複数ある場合にボタンテンプレートで選択肢を提示
- 複数のLINEチャンネルに対応可能

## 始め方

### 必要条件

- Python 3.6以上
- Flask
- LINE Messaging API SDK for Python

### インストール

1. このリポジトリをクローンまたはダウンロードします。

```bash
git clone https://your-repository-url.git
cd your-repository-directory
```

2. 必要なパッケージをインストールします。

```
pip install -r requirements.txt
```


### 設定

1. `config.json` ファイルを作成し、以下の形式でLINEチャンネルのアクセストークンとシークレットを設定します。

```json
{
    "your_channel_name": {
    "channel_access_token": "YOUR_CHANNEL_ACCESS_TOKEN",
    "channel_secret": "YOUR_CHANNEL_SECRET",
    "botanswer": "BOTANSWER_JSON_PATH",
    "search_word": "WORDS_TO_BE_ADDED_IN_SEARCH"
  }
// 他のチャンネルの設定も同様に追加可能
}
```

* botanswer: 回答データが記載されたjsonファイルのパスを記載します。jsonの中身はdata/botanswer_sample.jsonを参考にしてください。
* search_word: 質問に対する検索結果が得られなかった場合にgoogle検索リンクを作成する機能において、検索ワードに追加する単語を+区切りで記載します（例：犬+大丈夫）

### 実行

以下のコマンドでサーバーを起動します。

```bash
python main.py --config_path "./config.json" --port 5001
```


## Webhookの設定

LINE Developersコンソールで、Webhook URLを以下の形式で設定します。

```
https://your-server-domain.com/<your_channel_name>/callback
```
