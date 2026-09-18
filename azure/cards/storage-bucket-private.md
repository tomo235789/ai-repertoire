---
id: storage-bucket-private
lang: azure
title: 公開アクセスを禁止したオブジェクトストレージのバケットを作る
tags: [ストレージ, 非公開, 暗号化, ネットワーク制限, storage-account, private, encryption, network-acl]
lib: azure.storage
fn: private_container_config
since: "2024"
verified: 2026-09-19
status: public
---

「誰にも公開しない、共有キーも使わせない、指定した ID だけが読める」という要求から、ストレージアカウントとコンテナとロール割り当ての設定を組み立てる。API は呼ばない。

## Signature

```python
def private_container_config(account_name: str, container_name: str, location: str, *, subscription_id: str, resource_group: str, key_vault_key_uri: str | None = None, encryption_identity_id: str | None = None, reader_principal_ids=(), reader_principal_type: str = 'ServicePrincipal', tags: dict[str, str] | None = None, allowed_ip_rules=()) -> dict
```

## Usage

```python
cfg = private_container_config(
    "examplestorage", "private-data", "japaneast",
    subscription_id="<sub>", resource_group="example-rg",
    reader_principal_ids=["11111111-2222-3333-4444-555555555555"],
)
storage.storage_accounts.begin_create("example-rg", "examplestorage", cfg["account"])
storage.blob_containers.create(**cfg["container"])
for a in cfg["role_assignments"]:
    auth.role_assignments.create(a["scope"], a["role_assignment_name"], a["parameters"])
```

## Contract

- 公開アクセスは三箇所で塞ぐ。`allowBlobPublicAccess` は `False`、`networkAcls.defaultAction` は `"Deny"`、コンテナの `publicAccess` は `"None"`
- `allowSharedKeyAccess` は `False`。アクセスキーと SAS ではなく Entra ID の認証だけを通す
- `minimumTlsVersion` は `"TLS1_2"`、`supportsHttpsTrafficOnly` は `True`
- `requireInfrastructureEncryption` は常に `True`
- `key_vault_key_uri` を渡すと `keySource` が `"Microsoft.Keyvault"` になり、鍵の URI が `keyvaulturi` / `keyname` / `keyversion` に分かれて入る。省略すると Microsoft 管理鍵
- 顧客管理鍵には `encryption_identity_id`（ユーザー割り当て ID の ARM リソース ID）が必須。アカウントの `identity` が `UserAssigned` になり、`encryption.identity` にも同じ ID が入る。その ID に Key Vault の Crypto Service Encryption User を先に与えておく
- `allowed_ip_rules` が空なら `publicNetworkAccess` は `"Disabled"`。1 件でもあると `"Enabled"` になるが、既定動作は `Deny` のまま
- `reader_principal_ids` には Storage Blob Data Reader をコンテナのスコープで割り当てる。割り当て名はスコープとプリンシパルから `uuid5` で決まる
- ロール定義 ID はサブスクリプションスコープで作る。割り当て先だけがコンテナのスコープ
- `reader_principal_type` は `User` / `Group` / `ServicePrincipal`。既定はサービスプリンシパル
- `ValueError`: アカウント名が小文字英数字 3〜24 文字でない、コンテナ名の形式違い、鍵の URI が `https://<vault>/keys/<name>[/<version>]` の形でない、顧客管理鍵にユーザー割り当て ID が無い、未知のプリンシパル種別、`allUsers` / `allAuthenticatedUsers` を読み取りに指定
- 引数を変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/storage-bucket-private.py` — S3 のパブリックアクセスブロックとバケットポリシー
- `gcp/examples/storage-bucket-private.py` — `public_access_prevention` と均一バケットレベルアクセス
- Terraform の同じ id のモジュール。宣言で書きたいときはこちら
- 一時的な共有が要るならコンテナを公開せず、ユーザー委任 SAS を短い期限で発行する

## Pitfalls

- ストレージアカウント名は **Azure 全体で一意**。リージョンやリソースグループとは無関係に衝突する
- `allowSharedKeyAccess=False` にすると接続文字列とアクセスキーを使う既存コードが全部落ちる。`DefaultAzureCredential` への移行が先
- `publicNetworkAccess="Disabled"` はポータルからの閲覧も塞ぐ。運用端末からの確認にはプライベートエンドポイントか IP 例外が要る
- 顧客管理鍵はアカウント作成と同時には設定できない。システム割り当て ID は作成後にしか決まらないので、先にアカウントを作って ID に Key Vault の Crypto Service Encryption User を与え、それから暗号化を設定する。同時に済ませたいならユーザー割り当て ID を先に作って使う
- `requireInfrastructureEncryption` はアカウント作成後に変更できない

## Test

`examples/storage-bucket-private_test.py`
