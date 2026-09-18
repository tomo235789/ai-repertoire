---
id: cdn-static-site
lang: azure
title: 静的サイトを CDN 経由で HTTPS 配信する
tags: [FrontDoor, CDN, キャッシュ, セキュリティヘッダー, front-door, cdn, cache, security-headers]
lib: azure.cdn
fn: static_site_config
since: "2024"
verified: 2026-09-19
status: public
---

「静的サイトを CDN から HTTPS で配り、HTML だけは短く持つ」という要求から Front Door のオリジン・ルート・応答ヘッダーを組み立てる。API は呼ばない。

## Signature

```python
def static_site_config(origin_host: str, *, origin_group_id: str, custom_domain: str | None = None, cache_seconds: int = 86400, html_cache_seconds: int = 60, compress: bool = True) -> dict
```

## Usage

```python
cfg = static_site_config(
    "examplestorage.z11.web.core.windows.net",
    origin_group_id=origin_group_id,
    custom_domain="www.example.com",
)
client.afd_origins.begin_create(
    "example-rg", "example-fd", "static-origin-group", "storage", cfg["origin"]
).result()
```

## Contract

- `httpsRedirect` は `"Enabled"`、`forwardingProtocol` は `"HttpsOnly"`、`minimumTlsVersion` は `"TLS1_2"`
- オリジンへの接続も証明書名の検査つき
- 応答ヘッダーはヘッダー名順に並び、HSTS・`nosniff`・Referrer-Policy・CSP が必ず入る
- キャッシュ規則は 2 本。HTML は `html_cache_seconds`、資産は `cache_seconds`
- `custom_domain` を渡すと既定ドメインへの紐付けが `"Disabled"` になる
- クエリ文字列ではキャッシュを分けない
- `originGroup.id` にはオリジングループの ARM リソース ID がそのまま入る。名前だけでは参照できない
- `ValueError`: ホスト名や独自ドメインの形式違い、オリジングループが ARM リソース ID でない、キャッシュ秒数が負、HTML のキャッシュが資産より長い
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/cdn-static-site.py` — CloudFront ディストリビューションとオリジンアクセス制御
- `terraform/modules/cdn-static-site` — 同じ構成を宣言で書くモジュール
- `gcp/examples/cdn-static-site.py` — Cloud CDN とバックエンドバケット
- 独自ドメインも CDN も要らないなら、ストレージの静的 Web サイトをそのまま公開する

## Pitfalls

- HTML を長くキャッシュすると、差し替えても古い画面が残る。資産はファイル名にハッシュを付けて長く、HTML は短くする
- 独自ドメインは証明書の検証（DNS の TXT レコード）が終わるまで有効にならない
- オリジンをストレージにする場合、Front Door からの経路だけを許すようにプライベートリンクかアクセス制限を別に設定する。設定しないとオリジンの URL に直接アクセスできる
- キャッシュの削除は即時ではない。反映を待てない変更はパスを変える
- クエリ文字列を無視する設定は、クエリで内容が変わるページには使えない

## Test

`examples/cdn-static-site_test.py`
