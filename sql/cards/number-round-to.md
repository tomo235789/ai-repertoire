---
id: number-round-to
lang: sql
title: 数値を指定した小数桁数で四捨五入する
tags: [四捨五入, 小数桁, 丸め, 表現誤差, round, precision, decimal-places, half-away-from-zero]
lib: sqlite
fn: ROUND
since: "3.0"
verified: 2026-09-17
status: public
---

小数第 n 位で丸める。`.5` はゼロから遠い方へ（一般的な四捨五入）。ただし浮動小数の表現誤差と、負の桁・返り値の型の扱いが方言で違う。

## Signature

```sql
ROUND(x, n)
```

## Usage

```sql
SELECT ROUND(1.2345, 2), ROUND(2.5), ROUND(-2.5), ROUND(2.675, 2), ROUND(1250, -2);
-- sqlite => (1.23, 3.0, -3.0, 2.67, 1250.0)   -- 常に REAL。負の桁は無視。2.67 は 3.43 以降（3.37 は 2.68）
-- duckdb => (1.23, 3, -3, 2.68, 1300)         -- DECIMAL リテラルなので 2.675 が正確
```

## Contract

- `.5` はゼロから遠い方へ丸める（half away from zero）。sqlite / duckdb とも `ROUND(2.5)` → `3`、`ROUND(-2.5)` → `-3`、`ROUND(0.5)` → `1`。偶数丸め（銀行家の丸め）ではない
- 表現誤差: sqlite は浮動小数（REAL）で丸めるので `ROUND(2.675, 2)` → `2.67`、`ROUND(1.005, 2)` → `1.0`、`ROUND(1.45, 1)` → `1.4`（2 進数では `2.67499…` のため）。ただしこれは 3.43.0 以降の結果（3.43.0 / 3.43.1 / 3.43.2 / 3.44.2 / 3.45.1 / 3.53.4 で確認）で、3.42.0 以前（3.37.2 / 3.42.0 で確認）では `2.68` / `1.01` / `1.5` と 10 進の見た目どおりに丸まる。版で結果が変わる値なので、テストや突き合わせでは版を固定するか値を避ける。duckdb は数値リテラルが DECIMAL なので `ROUND(2.675, 2)` → `2.68`、`ROUND(1.005, 2)` → `1.01`。duckdb の DOUBLE 列は `ROUND(2.675::DOUBLE, 2)` → `2.68` だが `ROUND(1.005::DOUBLE, 2)` → `1.0` と、値によって誤差が残る
- 返り値の型: sqlite は常に REAL（`ROUND(3)` → `3.0`、`ROUND(2.5, 0)` → `3.0`）。duckdb は入力の型に従う（DECIMAL → 小数 n 桁の DECIMAL、DOUBLE → DOUBLE、INTEGER → INTEGER）
- 負の桁: sqlite は無視して 0 として扱う（`ROUND(1250, -2)` → `1250.0`、`ROUND(2.5, -1)` → `3.0`）。duckdb は 10 の位・100 の位で丸める（`ROUND(1250, -2)` → `1300`、`ROUND(25, -1)` → `30`、`ROUND(-25, -1)` → `-30`）
- `n` を省くと `0`。`x` か `n` が `NULL` なら `NULL`
- duckdb は `n` に小数を渡すと Binder Error。sqlite は整数に切り捨てて使う

## Alternatives

- PostgreSQL: `ROUND(x, 2)` は `numeric` 専用で、`double precision` は `ROUND(x::numeric, 2)` と書く。MySQL / BigQuery: `ROUND(x, 2)`。BigQuery は `ROUND(x, 2, 'ROUND_HALF_EVEN')` で偶数丸めを指定できると書かれる
- 桁を揃えた表示用の文字列は `printf('%.2f', x)`（sqlite、duckdb とも可）。ただし丸め方向が違い、sqlite の `printf('%.0f', 2.5)` は `'3'`（3.53.4 で確認。3.43.2〜3.45.1 では `'2'`、`3.5` が `'3'` になる版があり、3.45.3 以降で `'3'` / `'4'` に戻った）、duckdb の `printf('%.0f', 2.5::DOUBLE)` は `'2'`（C の printf と同じ偶数丸め）。`printf('%.2f', 2.675)` も `ROUND` と同じく 3.43 以降は `'2.67'`、3.37 は `'2.68'`
- 偶数丸めが要るなら duckdb の `ROUND_EVEN(x, n)`。sqlite には無い
- 切り捨て・切り上げは `FLOOR` / `CEIL`、ゼロ方向の切り捨ては `TRUNC(x)`（sqlite 3.35+ / duckdb）。`CAST(x AS INTEGER)` は sqlite ではゼロ方向の切り捨て（`-2.7` → `-2`）だが、duckdb では四捨五入（`-2.7` → `-3`、`2.5` → `3`）なので切り捨て目的で使わない
- 金額など誤差を許容できない値は整数（最小単位）か DECIMAL 型で持つ

## Pitfalls

- Python の `round` は偶数丸め（`round(2.5)` → `2`）、TypeScript（es-toolkit の `round`）は正の無限大方向（`round(-2.5)` → `-2`）、SQL はゼロから遠い方（`-3`）。`.5` ちょうどの値で 3 者とも結果が違う
- `2.675` の表現誤差は sqlite 3.43 以降と Python で同じ方向（`2.67`）に出るが、sqlite 3.37 と duckdb（DECIMAL）は `2.68`。「DB で丸めた値」と「アプリで丸めた値」を突き合わせると食い違う
- sqlite は負の桁を黙って無視する。100 円単位の丸めは `ROUND(x / 100.0) * 100` と書く。`x / 100` だと `x` が INTEGER のとき `ROUND` の前に整数除算で切り捨てられ、`1550` が `1500.0` になる（duckdb の `/` は実数除算なので `1600` だが、移植を考えて `100.0` にしておく）
- sqlite の返り値は REAL なので `ROUND(3)` を文字列にすると `'3.0'`。整数が欲しいなら `CAST(ROUND(x) AS INTEGER)`

## Test

`examples/number-round-to_test.py`
