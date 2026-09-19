---
id: iam-least-privilege-role
lang: gcp
title: 特定の操作だけを許可する最小権限のロールを作る
tags: [カスタムロール, 最小権限, 権限, 権限昇格, custom-role, least-privilege, permissions, escalation]
lib: gcp.iam
fn: least_privilege_role
since: "2024"
verified: 2026-09-19
status: public
---

「この権限だけを集めたロールを作る」という要求からカスタムロールを組み立てる。権限昇格につながる権限は明示しないと混ぜられない。API は呼ばない。

## Signature

```python
def least_privilege_role(role_id: str, title: str, permissions, *, description: str = '', stage: str = 'GA', allow_privilege_escalation: bool = False) -> dict
```

## Usage

```python
cfg = least_privilege_role(
    "objectLister", "Object Lister", ["storage.objects.list", "storage.objects.get"]
)
service.projects().roles().create(
    parent="projects/my-project",
    body={"roleId": cfg["role_id"], "role": cfg["role"]},
).execute()
```

## Contract

- `includedPermissions` は重複を除いて名前順に並ぶ
- `stage` の既定は `"GA"`
- `role_id` は `role` の外に返る。作成時の `roleId` にそのまま渡せる
- `PRIVILEGE_ESCALATING_PERMISSIONS` に当たる権限は `allow_privilege_escalation=True` なしでは `ValueError`
- `ValueError`: ロール ID が英数字・アンダースコア・ピリオドの 3〜64 文字でない、タイトルが空、権限が空、権限にワイルドカード、権限が `<サービス>.<リソース>.<動詞>` の形でない、未知のステージ
- 引数を変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/iam-least-privilege-role.py` — IAM ポリシードキュメント
- `azure/examples/iam-least-privilege-role.py` — カスタム RBAC ロール
- 事前定義ロールで足りるならカスタムロールは作らない。管理の手間が増えるだけ
- リソース単位で絞りたいならロールではなく IAM 条件（CEL）を使う

## Pitfalls

- カスタムロールに含められない権限がある。API によっては事前定義ロールでしか付与できない
- カスタムロールはプロジェクトか組織に属する。プロジェクトをまたいで同じロールを使い回せない
- 権限を足しても、その権限を持たないと自分ではロールに入れられない。作る側にも同じ権限が要る
- `iam.serviceAccounts.actAs` は一見無害だが、その ID になりすませる。実質的な権限昇格になる
- ロールを削除しても 7 日間は復活でき、その間 ID を再利用できない

## Test

`examples/iam-least-privilege-role_test.py`
