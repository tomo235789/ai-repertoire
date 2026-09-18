---
id: observability-alarm-error-rate
lang: gcp
title: エラー率のしきい値でアラームを発報する
tags: [CloudMonitoring, アラートポリシー, MQL, 通知チャネル, cloud-monitoring, alert-policy, mql, notification-channel]
lib: gcp.monitoring
fn: error_rate_alert
since: "2024"
verified: 2026-09-19
status: public
---

「5xx の割合が続けて高いときだけ人を起こす」という要求から Cloud Monitoring のアラートポリシーを組み立てる。クエリは組み立てるだけで実行しない。

## Signature

```python
def error_rate_alert(display_name: str, service_name: str, notification_channels, *, threshold_ratio: float = 0.05, alignment_seconds: int = 300, duration_seconds: int = 300, min_requests_per_interval: int = 20, auto_close_seconds: int = 86400, combiner: str = 'OR') -> dict
```

## Usage

```python
policy = error_rate_alert(
    "api エラー率", "example-api",
    ["projects/my-project/notificationChannels/1234567890"],
)
client.create_alert_policy(name="projects/my-project", alert_policy=policy)
```

## Contract

- 通知チャネルは重複を除いて名前順に並ぶ。空だと `ValueError`
- クエリは `align delta(...)` で刻みごとの**件数**を数える。`align rate(...)` は毎秒の値になり件数と比べられない
- `min_requests_per_interval` に満たない刻みを落としてから `failed / total` を出す
- `duration` は秒の文字列。継続時間は集計の刻み以上でなければ `ValueError`
- `alert_strategy` に自動クローズと、チャネルごとの再通知の間隔が入る。間隔は集計の刻みか 1800 秒の大きい方。`notification_rate_limit` はログベースの条件でしか効かないので使わない
- `documentation` にしきい値と足切りの件数が日本語で入る
- `ValueError`: 表示名やサービス名が空、通知チャネルが空、しきい値が 0 以下か 1.0 超、集計の刻みが既定の値以外、継続時間が刻み未満か 60 秒の倍数でない、最小件数が 1 未満、未知の combiner
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/observability-alarm-error-rate.py` — CloudWatch のメトリック数式アラーム
- `azure/examples/observability-alarm-error-rate.py` — スケジュールクエリのアラート規則
- サービスレベル目標として管理するならアラートポリシーではなく SLO とバーンレートアラートを使う
- ログの中身を条件にするならログベースの指標を先に作る

## Pitfalls

- 件数の足切りを入れないと、深夜の 1 件の失敗でエラー率 100% になる
- クエリは監視対象と指標に強く依存する。Cloud Run 以外に流用するときは `fetch` する監視対象を変える。実際の値は Metrics Explorer で確かめてから使う
- 通知チャネルを空にしたポリシーは発報しても誰にも届かない。作れてしまうので注意する
- 自動クローズを短くすると、復旧していないのにインシデントが閉じる
- 指標の取り込みに数分の遅れがある。発報も同じだけ遅れる

## Test

`examples/observability-alarm-error-rate_test.py`
