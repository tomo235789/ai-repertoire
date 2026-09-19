---
id: iam-least-privilege-role
lang: azure
title: 特定の操作だけを許可する最小権限のロールを作る
tags: [カスタムロール, 最小権限, RBAC, 操作, custom-role, least-privilege, rbac, actions]
lib: azure.authorization
fn: least_privilege_role
since: "2024"
verified: 2026-09-19
status: public
---

「この操作だけを、このスコープでだけ許す」という要求から、カスタムロール定義を組み立てる。`role_definitions.create_or_update` にそのまま渡せる。API は呼ばない。

## Signature

```python
def least_privilege_role(role_name: str, description: str, actions, assignable_scopes, *, data_actions=(), not_actions=(), not_data_actions=()) -> dict
```

## Usage

```python
SCOPE = "/subscriptions/<sub>/resourceGroups/example-rg"
READ = "Microsoft.Storage/storageAccounts/blobServices/containers/read"

cfg = least_privilege_role("Blob Lister", "コンテナ一覧だけ", [READ], [SCOPE])
client.role_definitions.create_or_update(
    SCOPE, cfg["role_definition_id"], cfg["role_definition"]
)
```

## Contract

- `permissions` は常に 1 ブロックで、`actions` / `notActions` / `dataActions` / `notDataActions` の 4 キーがすべて list として入る
- `type` は常に `"CustomRole"`
- `role_definition_id` は role_name と先頭の割り当てスコープから `uuid5` で決まる。同じ入力なら同じ ID になり、作り直しても定義が重複しない
- 管理プレーンの `actions` が空でも、`data_actions` があればロールを作れる
- `ValueError`: actions と data_actions が両方空、assignable_scopes が空、スコープが `/subscriptions/` でも管理グループでもない、管理グループが 2 件以上、データプレーンの操作と管理グループの併用、`*` や `Microsoft.Storage/*` のような広すぎるワイルドカード、`PRIVILEGE_ESCALATING_ACTIONS` に当たる操作（`Microsoft.Authorization/*/write` のようにワイルドカードで一致する形も含む）、actions と not_actions（data 側も同様）の重複
- 引数のリストを変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/iam-least-privilege-role.py` — IAM ポリシードキュメント。Azure と違い Allow/Deny を文で書く
- 組み込みロールで足りるならカスタムロールは作らない。`iam-read-only-policy` の `built_in_reader_role_id` を使う
- 属性ベースの絞り込みが要るなら、ロールではなく ABAC の条件式（`condition`）を使う

## Pitfalls

- `Microsoft.Storage/storageAccounts/*/read` のようにリソース種別まで絞ったワイルドカードは許すが、プロバイダ丸ごとの `Microsoft.Storage/*` は最小権限にならないので弾いている
- 管理プレーンの `actions` に Blob の読み取りは含まれない。データを読むには `data_actions` が要る。ここを取り違えるとポータルでは見えるのに SDK から読めない
- `assignable_scopes` はロールを**割り当てられる**範囲であって、権限が効く範囲ではない。実際の範囲はロール割り当て側のスコープで決まる
- データプレーンの操作を持つロールは管理グループに割り当てられない。サブスクリプション以下のスコープにする
- `Microsoft.Authorization/roleAssignments/write` などロールを書き換えられる操作を含めると、そのロールを持つ相手が自分で権限を増やせる。読み取り（`/read`）は通す
- カスタムロールの定義 ID はサブスクリプションごとに別物。テナントをまたいで同じ ID を使い回せない

## Test

`examples/iam-least-privilege-role_test.py`
