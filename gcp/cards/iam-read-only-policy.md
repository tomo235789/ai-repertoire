---
id: iam-read-only-policy
lang: gcp
title: 読み取り専用のアクセスポリシーを作る
tags: [IAMポリシー, 閲覧者, 条件付きバインディング, 同時更新, iam-policy, viewer, condition, etag]
lib: gcp.iam
fn: read_only_policy
since: "2024"
verified: 2026-09-19
status: public
---

「見るだけの権限を、この相手に、この条件で」という要求から IAM ポリシーを組み立てる。公開メンバーと書き込みできるロールは弾く。API は呼ばない。

## Signature

```python
def read_only_policy(bindings: dict[str, list[str]], *, etag: str | None = None, condition_expression: str | None = None, condition_title: str = '', allow_custom_roles: bool = False) -> dict
```

## Usage

```python
current = bucket.get_iam_policy(requested_policy_version=3)
addition = read_only_policy(
    {"roles/storage.objectViewer": ["serviceAccount:app@my-project.iam.gserviceaccount.com"]},
    etag=current.etag,
)
for b in addition["bindings"]:                  # 全置換ではなく既存に足す
    current[b["role"]] = set(current.get(b["role"], [])) | set(b["members"])
bucket.set_iam_policy(current)
```

## Contract

- `version` は常に 3。条件付きバインディングを扱える版
- バインディングはロール名順、メンバーは重複を除いて名前順に並ぶ
- `etag` は渡したときだけ入る
- 条件を付けるときは式と名前の両方が要る。片方だけだと `ValueError`。条件は全バインディングに付く
- `ValueError`: バインディングが空、メンバーが空、ロールやメンバーの形式違い、`allUsers` / `allAuthenticatedUsers`、`roles/editor` などの広いロール、閲覧者でない事前定義ロール、許可していないカスタムロール
- カスタムロール（`projects/<id>/roles/...`）は既定で `ValueError`。中身が読み取り専用かを名前からは判断できないため、確かめたうえで `allow_custom_roles=True` を明示する
- 引数を変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/iam-read-only-policy.py` — `Get*` / `List*` / `Describe*` のポリシー文書
- `azure/examples/iam-read-only-policy.py` — プロバイダ単位の `*/read` ロール
- プロジェクト全体を見せてよいなら `roles/viewer` をそのまま使う
- 権限を絞り込みたいなら `iam-least-privilege-role` でカスタムロールを作る

## Pitfalls

- `set_iam_policy` は全置換。読み込んだポリシーに足してから渡さないと既存のバインディングが消える
- `etag` を渡さないと、他の人の変更を上書きしうる。取得したポリシーの etag を必ず添える
- 条件付きバインディングは `version: 3` で読み書きする。`requested_policy_version` を上げずに読むと条件が落ちる
- `roles/viewer` はプロジェクト内のほぼ全リソースのメタデータを読める。設定値に秘密が入っていると見えてしまう
- IAM の変更が全域に行き渡るまで数分かかる。直後の検証は失敗しうる
- `allow_custom_roles=True` にすると中身は検証されない。書き込み権限を含むカスタムロールを渡せば、読み取り専用のつもりのポリシーに書き込みが混ざる

## Test

`examples/iam-read-only-policy_test.py`
