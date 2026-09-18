---
id: cdn-static-site
lang: gcp
title: 静的サイトを CDN 経由で HTTPS 配信する
tags: [CloudCDN, バックエンドバケット, マネージド証明書, キャッシュ, cloud-cdn, backend-bucket, managed-certificate, cache]
lib: gcp.cdn
fn: static_site_config
since: "2024"
verified: 2026-09-19
status: public
---

「バケットの中身を CDN 越しに HTTPS で配り、平文は HTTPS へ寄せる」という要求から、バックエンドバケットから転送ルールまでの構成を組み立てる。API は呼ばない。

## Signature

```python
def static_site_config(name: str, bucket_name: str, domains, *, cache_mode: str = 'CACHE_ALL_STATIC', default_ttl_seconds: int = 3600, max_ttl_seconds: int = 86400, client_ttl_seconds: int = 300, enable_negative_caching: bool = True, serve_while_stale_seconds: int = 86400) -> dict
```

## Usage

```python
cfg = static_site_config("example-site", "example-bucket", ["www.example.com"])
compute.backendBuckets().insert(
    project="my-project", body=cfg["backend_bucket"]
).execute()
compute.urlMaps().insert(project="my-project", body=cfg["url_map"]).execute()
```

## Contract

- `enableCdn` は常に `True`
- `http_redirect` で平文のアクセスを HTTPS へ 301 で寄せる
- TLS ポリシーは `MODERN` プロファイルの TLS 1.2 以上
- 証明書はマネージド。ドメインは重複を除いて名前順に並ぶ
- 各リソースは名前で繋がる。URL マップはバックエンドバケット、プロキシは URL マップと証明書、転送ルールはプロキシを指す
- HTTP から HTTPS へ寄せる側も、URL マップ・プロキシ・ポート 80 の転送ルールの 3 つを返す。URL マップだけでは受け口が無い
- `cacheKeyPolicy` は空。クエリ文字列でもヘッダーでもキャッシュを分けない
- `ValueError`: 名前やバケット名やドメインの形式違い、ドメインが空、未知のキャッシュモード、上限が既定未満、ブラウザ側の保持が既定超
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/cdn-static-site.py` — CloudFront ディストリビューション
- `azure/examples/cdn-static-site.py` — Front Door のオリジンとルート
- `terraform/modules/cdn-static-site` — 同じ構成を宣言で書くモジュール
- 独自ドメインが要らないならバケットを直接公開してもよい。ただし HTTPS とキャッシュは付かない

## Pitfalls

- マネージド証明書は、ドメインの A レコードが転送ルールの IP を指してから発行される。DNS を先に向けないと `PROVISIONING` のまま
- HTTP からの寄せには HTTPS とは別のプロキシと転送ルールが要る。HTTPS 側だけ作ると平文のアクセスは接続できずに落ちる
- キャッシュの削除（無効化）は即時ではない。反映を待てない変更はファイル名を変える
- 否定キャッシュを有効にすると 404 も保持される。バケットにファイルを追加した直後に 404 が残ることがある
- バケットを公開読み取りにする必要がある。公開したくない内容は署名付き URL か Cloud Run を挟む

## Test

`examples/cdn-static-site_test.py`
