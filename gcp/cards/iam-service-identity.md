---
id: iam-service-identity
lang: gcp
title: ワークロード用のサービス ID にリソースへのアクセスを与える
tags: [サービスアカウント, WorkloadIdentity, ロール付与, 鍵なし, service-account, workload-identity, binding, keyless]
lib: gcp.iam
fn: service_identity_config
since: "2024"
verified: 2026-09-19
status: public
---

「このワークロードに専用のサービスアカウントを作り、必要なロールだけ与える。鍵ファイルは作らない」という要求から設定を組み立てる。API は呼ばない。

## Signature

```python
def service_identity_config(project_id: str, account_id: str, roles, *, display_name: str = '', kubernetes_namespace: str | None = None, kubernetes_service_account: str | None = None, allow_privileged_roles: bool = False) -> dict
```

## Usage

```python
cfg = service_identity_config(
    "my-project", "app-runner", ["roles/storage.objectViewer"],
    kubernetes_namespace="prod", kubernetes_service_account="api",
)
iam.projects().serviceAccounts().create(
    name="projects/my-project", body=cfg["service_account"]
).execute()
add_bindings("projects/my-project", cfg["bindings"])   # 権限を与える
add_bindings(cfg["workload_identity_binding"]["resource"], [cfg["workload_identity_binding"]])
```

## Contract

- `email` は `<account_id>@<project_id>.iam.gserviceaccount.com`
- `bindings` はロール名順に並び、メンバーはこのサービスアカウント 1 件だけ。サービスアカウントを作るだけでは権限が付かないので、返り値のバインディングを別に適用する
- `display_name` を省略すると `account_id` がそのまま表示名になる
- `workload_identity_binding` は Kubernetes の名前空間とサービスアカウント名を両方渡したときだけ返る。片方だけだと `ValueError`
- `PRIVILEGED_ROLES` に当たるロールは `allow_privileged_roles=True` なしでは `ValueError`
- `ValueError`: プロジェクト ID やアカウント ID の形式違い、ロールが空、ロールの形式違い
- 鍵（サービスアカウントキー）は作らない
- 引数を変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/iam-service-identity.py` — 信頼ポリシー付きの IAM ロール
- `azure/examples/iam-service-identity.py` — マネージド ID へのロール割り当て
- GitHub Actions など外部からの認証は Workload Identity 連携でプールとプロバイダを作る
- 短期の権限借用で足りるなら専用アカウントを作らず `roles/iam.serviceAccountTokenCreator` を使う

## Pitfalls

- サービスアカウントキー（JSON）は作らない。漏れたら誰でもその ID になれる。Workload Identity か付与済みの実行環境の ID を使う
- Workload Identity のメンバー表記は `serviceAccount:<project>.svc.id.goog[<namespace>/<ksa>]`。先頭の `serviceAccount:` を落とすと無効。クラスタ側の注釈も合わせないと効かない
- サービスアカウントを消しても、同じ名前で作り直すと内部 ID が変わる。付与済みのバインディングは無効なまま残る
- `roles/iam.serviceAccountTokenCreator` と `roles/iam.serviceAccountUser` は、対象のサービスアカウント 1 つをリソースにして与える（`projects/<p>/serviceAccounts/<sa>` へのバインディング）。プロジェクトに与えるとプロジェクト内の全サービスアカウントになりすませるので、この関数は明示的な許可なしには通さない
- プロジェクトの既定サービスアカウントには編集者ロールが付いていることがある。組織ポリシー `constraints/iam.automaticIamGrantsForDefaultServiceAccounts` で抑止できる。いずれにせよワークロードには専用のものを作る

## Test

`examples/iam-service-identity_test.py`
