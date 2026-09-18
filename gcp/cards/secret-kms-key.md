---
id: secret-kms-key
lang: gcp
title: 顧客管理の暗号鍵を作って保存データを暗号化する
tags: [CloudKMS, キーリング, ローテーション, HSM, cloud-kms, key-ring, rotation, cmek]
lib: gcp.kms
fn: customer_managed_key
since: "2024"
verified: 2026-09-19
status: public
---

「自分の鍵で保存データを暗号化し、定期的に入れ替え、誤って破棄しても取り消せるようにする」という要求からキーリングと鍵と権限の設定を組み立てる。API は呼ばない。

## Signature

```python
def customer_managed_key(project_id: str, location: str, key_ring: str, key_name: str, *, next_rotation_time: str, protection_level: str = 'HSM', rotation_period_days: int = 90, destroy_scheduled_days: int = 30, encrypter_members=()) -> dict
```

## Usage

```python
cfg = customer_managed_key(
    "my-project", "asia-northeast1", "app-ring", "data-key",
    next_rotation_time="2026-12-18T00:00:00Z",
    encrypter_members=["serviceAccount:app@my-project.iam.gserviceaccount.com"],
)
client.create_key_ring(**cfg["key_ring"])
client.create_crypto_key(**cfg["crypto_key"])
```

## Contract

- `purpose` は常に `"ENCRYPT_DECRYPT"`、アルゴリズムは `"GOOGLE_SYMMETRIC_ENCRYPTION"`
- 保護レベルは `"SOFTWARE"` か `"HSM"`。既定は `"HSM"`
- ローテーション間隔と破棄待ちは秒の文字列。90 日なら `"7776000s"`
- `next_rotation_time` は必須。間隔だけを指定した鍵は Cloud KMS に拒否される。時刻を引数で受け取るので関数は純粋なまま
- 破棄待ちは 7 日以上。短くすると誤った破棄を取り消せない
- `iam_binding` のメンバーは重複を除いて名前順。ロールは `roles/cloudkms.cryptoKeyEncrypterDecrypter`
- `ValueError`: キーリング名や鍵名の形式違い、未知の保護レベル、ローテーション間隔が 1 日未満、破棄待ちが 7 日未満、メンバーが `<種別>:<識別子>` の形でない、次回ローテーション時刻が RFC 3339 でない
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/secret-kms-key.py` — KMS のカスタマーマネージドキー
- `azure/examples/secret-kms-key.py` — Key Vault の顧客管理鍵
- Google 管理の鍵で足りるなら鍵は作らない。`storage-bucket-private` の既定がそれ
- 鍵の材料を自分で持ち込むなら外部キーマネージャ（EXTERNAL）を使う。作成手順が変わるのでこの関数では扱わない

## Pitfalls

- キーリングと鍵は削除できない。作りすぎると消せないまま残る
- キーリングのロケーションは暗号化するデータと同じにする。違うと使えない組み合わせがある
- ローテーションしても、古い版で暗号化したデータは古い版で復号する。古い版を破棄してはいけない
- 鍵を使うサービスにはそれぞれの Google 管理サービスアカウントへ権限を与える。アプリのサービスアカウントだけでは足りない
- HSM の保護レベルは料金がソフトウェア鍵より高い。用途に応じて選ぶ
- 次回ローテーション時刻を過去にすると、作成した直後に 1 回ローテーションが走る

## Test

`examples/secret-kms-key_test.py`
