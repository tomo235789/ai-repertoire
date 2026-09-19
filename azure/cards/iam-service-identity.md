---
id: iam-service-identity
lang: azure
title: ワークロード用のサービス ID にリソースへのアクセスを与える
tags: [マネージドID, ロール割り当て, RBAC, 最小権限, managed-identity, role-assignment, rbac]
lib: azure.authorization
fn: service_identity_config
since: "2024"
verified: 2026-09-19
status: public
---

「このワークロードに、このスコープで、この組み込みロールだけを与える」という要求から、リソースに付ける `identity` ブロックと `role_assignments.create` に渡す引数を組み立てる。API は呼ばない。

## Signature

```python
def service_identity_config(principal_id: str, scope: str, *, role_name: str = 'Reader', user_assigned_identity_id: str | None = None, allow_privileged_role: bool = False) -> dict
```

## Usage

```python
from azure.mgmt.authorization import AuthorizationManagementClient

cfg = service_identity_config(
    "11111111-2222-3333-4444-555555555555",
    "/subscriptions/<sub>/resourceGroups/example-rg",
    role_name="Storage Blob Data Reader",
)
app_config["identity"] = cfg["identity"]
a = cfg["assignment"]
client.role_assignments.create(a["scope"], a["role_assignment_name"], a["parameters"])
```

## Contract

- `identity` はシステム割り当てなら `{"type": "SystemAssigned"}`、`user_assigned_identity_id` を渡すと `userAssignedIdentities` に ARM ID をキーとする空 dict が入る
- `roleDefinitionId` は割り当てスコープから取り出したサブスクリプション配下の `providers/Microsoft.Authorization/roleDefinitions/<GUID>`。GUID は `BUILT_IN_ROLES` の固定値。割り当て先のスコープ自体は引数のまま
- `role_assignment_name` は scope・principal_id・role_name から `uuid5` で決まる。同じ入力なら同じ名前になり、再実行しても割り当てが重複しない
- `principalType` は常に `"ServicePrincipal"`
- `ValueError`: principal_id が GUID でない、scope が `/subscriptions/` で始まらない、`BUILT_IN_ROLES` に無いロール名、`Owner` と `User Access Administrator` を `allow_privileged_role=True` なしで指定
- 同じ入力に同じ出力を返し、引数を変更せず、全体を `json.dumps` できる

## Alternatives

- `aws/examples/iam-service-identity.py` — 信頼ポリシー付きの IAM ロール。Azure と違いロールを引き受ける側を信頼ポリシーで書く
- `gcp/examples/iam-service-identity.py` — サービスアカウントへの IAM バインディング
- Terraform の `azurerm_role_assignment` は名前を省略すると内部で乱数の GUID を作る。冪等にしたいならこの関数と同じく名前を渡す

## Pitfalls

- `principal_id` はアプリケーション（クライアント）ID ではなく、マネージド ID の **オブジェクト ID**。取り違えると割り当ては成功して権限は効かない
- システム割り当て ID のオブジェクト ID はワークロードを作った後でないと決まらない。先に割り当てたいならユーザー割り当て ID を作ってから渡す
- ロール定義 GUID はテナントをまたいで固定だが、カスタムロールはサブスクリプションごとに GUID が変わる。この関数は組み込みロールだけを扱う
- サブスクリプションをスコープにすると、その配下の全リソースに効く。リソースグループや個々のリソースまで絞る
- ロール割り当ての反映は即時ではない。作成直後のアクセスは失敗しうる

## Test

`examples/iam-service-identity_test.py`
