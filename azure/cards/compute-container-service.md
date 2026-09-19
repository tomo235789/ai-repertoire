---
id: compute-container-service
lang: azure
title: コンテナを常駐サービスとして実行する
tags: [コンテナ, 常駐サービス, オートスケール, イングレス, container-apps, ingress, scale, managed-identity]
lib: azure.containerapps
fn: container_service_config
since: "2024"
verified: 2026-09-19
status: public
---

「このイメージを常駐させ、内部にだけ公開し、負荷で台数を変える」という要求から Container Apps の body を組み立てる。API は呼ばない。

## Signature

```python
def container_service_config(name: str, image: str, managed_environment_id: str, *, target_port: int = 8080, external_ingress: bool = False, cpu: float = 0.5, min_replicas: int = 1, max_replicas: int = 10, env: dict[str, str] | None = None, registry_server: str | None = None, registry_identity: str = 'system') -> dict
```

## Usage

```python
cfg = container_service_config(
    "example-api",
    "example.azurecr.io/api:1.4.2",
    "/subscriptions/<sub>/resourceGroups/example-rg"
    "/providers/Microsoft.App/managedEnvironments/example-env",
    registry_server="example.azurecr.io",
)
client.container_apps.begin_create_or_update(
    "example-rg", "example-api", {"location": "japaneast", **cfg}
).result()
```

## Contract

- `ingress.external` は既定で `False`。インターネット公開は引数で明示したときだけ
- `ingress.allow_insecure` は常に `False`。平文 HTTP は HTTPS にリダイレクトされる
- `traffic` は常に最新リビジョンへ 100%
- `resources.memory` は CPU コア数の 2 倍の GiB。`cpu=0.5` なら `"1Gi"`
- `registry_server` を渡したときだけ `registries` が入り、認証はマネージド ID。返り値にパスワードは含まれない
- `registry_identity` にユーザー割り当て ID の ARM リソース ID を渡すと、アプリの `identity` が `"SystemAssigned, UserAssigned"` になり、その ID が `userAssignedIdentities` にも入る。付けないとイメージの取得に失敗する
- `env` は名前順に並ぶ。同じ入力からは同じリビジョンになる
- `min_replicas=0` は許す。アイドル時の課金が止まる代わりに初回リクエストが遅くなる
- `ValueError`: 名前が英小文字・数字・ハイフンの 2〜32 文字でない、イメージにタグが無いかタグが空、タグが `latest`、ポートが 1〜65535 の外、CPU が 0.25 刻みの 2.0 までに無い、`min_replicas > max_replicas`、`registry_identity` が `"system"` でも ARM リソース ID でもない
- 引数を変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/compute-container-service.py` — ECS サービス。タスク定義とサービスを分けて書く
- `gcp/examples/compute-container-service.py` — Cloud Run サービス
- リクエスト単位で起動するだけなら `compute-serverless-function` の方が構成が少ない
- Kubernetes の細かい制御が要るなら Container Apps ではなく AKS

## Pitfalls

- `latest` タグはリビジョンごとに中身が変わる。ロールバックできなくなるのでこの関数は弾いている
- CPU とメモリは自由な組み合わせにできない。比が合わないとデプロイ時に拒否される
- `min_replicas=0` からのスケールアップにはコールドスタートがある。応答時間の要件があるなら 1 以上にする
- 秘密情報を `env` に入れない。`secrets` と `secretRef` を使うか `secret-fetch-at-runtime` のように実行時に取る
- マネージド環境は先に作っておく。この関数は環境の ARM ID を受け取るだけ

## Test

`examples/compute-container-service_test.py`
