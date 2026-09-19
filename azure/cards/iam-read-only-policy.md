---
id: iam-read-only-policy
lang: azure
title: 読み取り専用のアクセスポリシーを作る
tags: [読み取り専用, ロール定義, RBAC, データプレーン, read-only, role-definition, rbac, data-actions]
lib: azure.authorization
fn: read_only_role
since: "2024"
verified: 2026-09-19
status: public
---

「このプロバイダの情報を見るだけ。書き換えも鍵の取得もさせない」という要求からロール定義を組み立てる。組み込み Reader で足りるときはその定義 ID を返す関数を使う。API は呼ばない。

## Signature

```python
def read_only_role(role_name: str, providers, assignable_scopes, *, description: str = '読み取り専用', data_read_actions=()) -> dict
def built_in_reader_role_id(scope: str) -> str
```

## Usage

```python
SCOPE = "/subscriptions/<sub>/resourceGroups/example-rg"

cfg = read_only_role("Storage Reader", ["Microsoft.Storage"], [SCOPE])
client.role_definitions.create_or_update(
    SCOPE, cfg["role_definition_id"], cfg["role_definition"]
)

# 組み込み Reader で足りるなら定義を作らずこれを割り当てる
reader_id = built_in_reader_role_id(SCOPE)
```

## Contract

- `actions` はプロバイダごとの `"<Provider>/*/read"` だけ。プロバイダ名順に並ぶので、引数の順序が違っても同じ定義になる
- `notActions` には Key Vault の鍵と秘密の読み取りが常に入る
- `dataActions` は空。データプレーンの読み取りは `data_read_actions` で明示したときだけ入り、`/read` で終わらない操作は `ValueError`
- `role_definition_id` はロール名と先頭スコープから `uuid5` で決まる。作り直しても定義が重複しない
- `built_in_reader_role_id` はスコープからサブスクリプション ID を取り出し、`/subscriptions/<id>/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7` を返す
- `ValueError`: providers か assignable_scopes が空、プロバイダ名が `Microsoft.<名前>` でない、スコープが `/subscriptions/` で始まらない
- 引数を変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/iam-read-only-policy.py` — `Get*` / `List*` / `Describe*` を並べたポリシー文書
- `gcp/examples/iam-read-only-policy.py` — `roles/viewer` へのバインディング
- 監査ログまで読ませたいなら Reader ではなく Monitoring Reader を足す
- 全リソースの参照でよければカスタムロールを作らず組み込み Reader をそのまま割り当てる

## Pitfalls

- 管理プレーンの `*/read` に `listKeys` は含まれない。あれは `/read` ではなく `/action` なので、Reader でもアクセスキーは取れない。逆に「Reader なら安全」と考えて `listKeys` を別に許すと読み取り専用ではなくなる
- 管理プレーンの読み取りだけでは Blob の中身は読めない。データを読むには `dataActions` が要る
- Reader はリソースの構成を見られる。接続文字列や環境変数を構成に直接書いていると、その値も見えてしまう
- `assignable_scopes` は割り当て**できる**範囲であって、権限が効く範囲ではない
- ロール定義はサブスクリプションに置かれる。リソースグループのスコープに続けた ID では割り当てが失敗する

## Test

`examples/iam-read-only-policy_test.py`
