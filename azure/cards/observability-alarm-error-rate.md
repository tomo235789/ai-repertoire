---
id: observability-alarm-error-rate
lang: azure
title: エラー率のしきい値でアラームを発報する
tags: [アラート, エラー率, KQL, アクショングループ, alert, error-rate, kusto, action-group]
lib: azure.monitor
fn: error_rate_alert
since: "2024"
verified: 2026-09-19
status: public
---

「失敗の割合が続けて高いときだけ人を起こす」という要求からスケジュールクエリのアラート規則を組み立てる。クエリは組み立てるだけで実行しない。

## Signature

```python
def error_rate_alert(name: str, scope_id: str, action_group_id: str, *, threshold_percent: float = 5.0, window_minutes: int = 15, evaluation_minutes: int = 5, min_requests: int = 20, severity: int = 1, auto_mitigate: bool = True) -> dict
```

## Usage

```python
props = error_rate_alert("error-rate", app_insights_id, action_group_id)
client.scheduled_query_rules.create_or_update(
    "example-rg", "error-rate", {"location": "japaneast", "properties": props}
)
```

## Contract

- 既定は 15 分の集計期間、5 分ごとの評価、エラー率 5% 超で発報
- 期間は ISO 8601 の duration。60 分の倍数は `"PT1H"` のように時間で表す
- クエリは `min_requests` に満たない期間を落とす。少ない件数で 100% にならない
- `auto_mitigate` は既定で `True`。回復すると自動で解決扱いになる
- `ValueError`: 名前が空、監視対象か通知先が `/subscriptions/<id>/resourceGroups/<rg>/providers/...` の形でない、整数であるべき引数が整数でない、しきい値が 0 以下か 100 超、集計期間か評価間隔が許可された値以外、評価間隔が集計期間より長い、最小件数が 1 未満、重大度が 0〜4 の外
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/observability-alarm-error-rate.py` — CloudWatch のメトリック数式アラーム
- `gcp/examples/observability-alarm-error-rate.py` — Cloud Monitoring のアラートポリシー
- メトリックだけで足りるならクエリ規則ではなくメトリックアラートの方が安く速い
- ログの中身を条件にするなら `observability-structured-logs` で項目を出してからクエリで絞る

## Pitfalls

- 件数の足切りを入れないと、深夜のアクセス 1 件が失敗しただけでエラー率 100% になる
- クエリ規則はログの取り込み遅延ぶん遅れて評価される。数分の遅れは避けられない
- 集計期間より評価間隔を短くすると、同じデータを何度も評価して同じアラートが続けて出る
- `auto_mitigate` を切ると、回復しても手で解決するまでアラートが残る
- 重大度 0 は最重大。既定を 0 にすると本当に重い事象と区別が付かなくなる

## Test

`examples/observability-alarm-error-rate_test.py`
