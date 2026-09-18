---
id: secret-kms-key
lang: azure
title: 顧客管理の暗号鍵を作って保存データを暗号化する
tags: [KeyVault, 顧客管理鍵, HSM, ローテーション, key-vault, cmk, hsm, rotation]
lib: azure.keyvault
fn: customer_managed_key
since: "2024"
verified: 2026-09-19
status: public
---

「保存データを自分の鍵で暗号化し、鍵は定期的に入れ替え、消せないようにする」という要求から、コンテナーと鍵とローテーションポリシーの設定を組み立てる。API は呼ばない。

## Signature

```python
def customer_managed_key(vault_name: str, key_name: str, location: str, *, tenant_id: str, key_type: str = 'RSA-HSM', key_size: int = 3072, rotation_period_days: int = 365, expiry_days: int = 730, purge_protection: bool = True, soft_delete_retention_days: int = 90) -> dict
```

## Usage

```python
cfg = customer_managed_key("example-kv", "data-key", "japaneast", tenant_id=tenant)
client.vaults.begin_create_or_update("example-rg", "example-kv", cfg["vault"]).result()
client.keys.create_if_not_exist("example-rg", "example-kv", "data-key", cfg["key"])
```

## Contract

- コンテナーは RBAC 認可・論理削除・消去保護が常に有効で、`publicNetworkAccess` は `"Disabled"`、ネットワーク既定動作は `"Deny"`
- SKU は HSM 鍵なら `premium`、ソフトウェア鍵なら `standard`
- `keyOps` は `wrapKey` / `unwrapKey` / `encrypt` / `decrypt` の 4 つだけ。署名には使えない
- 鍵は `exportable: False`。取り出せない
- ローテーションは作成から `rotation_period_days` 経った時点で走る（`timeAfterCreate`）。期限からの逆算では最初の版が回らない。期限 30 日前に通知が入る
- `ValueError`: 名前の形式違い、鍵の種類が RSA / RSA-HSM 以外、鍵長が 3072 / 4096 以外、論理削除の保持日数が 7〜90 の外、ローテーション間隔が 7 日未満、有効期間が 28 日未満かローテーション間隔以下、`purge_protection=False`
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/secret-kms-key.py` — KMS のカスタマーマネージドキーとキーポリシー
- `gcp/examples/secret-kms-key.py` — Cloud KMS のキーリングと暗号鍵
- 鍵の管理を任せてよいなら Microsoft 管理鍵で十分。`storage-bucket-private` の既定がそれ
- 鍵の材料まで自前で持ち込むならマネージド HSM に BYOK でインポートする

## Pitfalls

- 消去保護は一度有効にすると無効に戻せない。逆に切ったまま運用すると、鍵を消された時点で暗号化データが読めなくなる
- 鍵をローテーションしても、古い版で暗号化されたデータは古い版で復号される。古い版を消してはいけない
- 顧客管理鍵を使うリソースには、コンテナーに対する Key Vault Crypto Service Encryption User が要る。先に与えないと暗号化の設定が失敗する
- `public_network_access="Disabled"` のコンテナーは、プライベートエンドポイントか信頼されたサービスの経路が無いと誰からも使えない
- 鍵の有効期限が切れると暗号化操作が止まる。ローテーション間隔と有効期間の差は余裕を持たせる

## Test

`examples/secret-kms-key_test.py`
