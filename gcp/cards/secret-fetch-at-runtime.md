---
id: secret-fetch-at-runtime
lang: gcp
title: 秘密情報を実行時にシークレット管理サービスから取得する
tags: [SecretManager, secretKeyRef, バージョン固定, アクセサ, secret-manager, secret-key-ref, version, accessor]
lib: gcp.secretmanager
fn: runtime_secret_config
since: "2024"
verified: 2026-09-19
status: public
---

「パスワードを設定に置かず、起動時に Secret Manager から注入する」という要求から、Cloud Run の参照と必要な IAM バインディングを組み立てる。秘密の値そのものは扱わない。

## Signature

```python
def secret_version_name(project_id: str, secret_id: str, version: str = 'latest') -> str
def runtime_secret_config(project_id: str, secrets: dict[str, str], service_account: str, *, pin_versions: dict[str, str] | None = None) -> dict
```

## Usage

```python
cfg = runtime_secret_config(
    "my-project", {"DB_PASSWORD": "db-password"},
    "app-runner@my-project.iam.gserviceaccount.com",
)
service.template.containers[0].env = cfg["env"]
for b in cfg["iam_bindings"]:
    grant(b["resource"], b["role"], b["members"])
```

## Contract

- `env` には `secret_key_ref` だけが入る。秘密の値は返り値に一切入らない
- 環境変数は名前順に並ぶ
- `pin_versions` で指定した環境変数はそのバージョンに固定され、他は `"latest"`
- `iam_bindings` はシークレットごとに 1 件。ロールは `roles/secretmanager.secretAccessor`
- `secret_version_name` は `projects/<p>/secrets/<s>/versions/<v>` を返す
- `ValueError`: プロジェクト ID やシークレット名の形式違い、バージョンが `"latest"` でも正の整数でもない、`secrets` が空、環境変数名が大文字とアンダースコア以外、サービスアカウントがメールアドレスでない、`pin_versions` に `secrets` に無いキーがある
- 引数を変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/secret-fetch-at-runtime.py` — Secrets Manager からの取得
- `azure/examples/secret-fetch-at-runtime.py` — Key Vault 参照
- ボリュームとしてマウントしたいなら環境変数ではなく `volumeMounts` で同じシークレットを指す
- SDK で直接読むなら参照を使わず `SecretManagerServiceClient` を組む

## Pitfalls

- 環境変数への注入は起動時に一度だけ。秘密を更新しても新しいリビジョンを出すまで古い値のまま
- `latest` は新しいリビジョンが起動するときに解決し直される。壊れた版を作ると、以後に起動したインスタンスだけが起動に失敗し、原因が見えにくい。版の入れ替えを検証してから配りたいなら `pin_versions` で固定する
- アクセサのロールはシークレット単位で与える。プロジェクト単位で与えると全部のシークレットが読める
- シークレットを消しても、バージョンを破棄するまでは課金される
- 環境変数はプロセス一覧や監視の出力に出ることがある。ログに環境変数を吐かない

## Test

`examples/secret-fetch-at-runtime_test.py`
