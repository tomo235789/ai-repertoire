"""http-pagination-cursor: ジェネレータによるカーソル式ページネーションの Contract を検証する。"""

import inspect
from collections.abc import Callable, Iterator
from typing import Any

import pytest

Page = dict[str, Any]


def paginate(fetch_page: Callable[[str | None], Page]) -> Iterator[Any]:
    """カードの Usage と同じ関数。"""
    cursor = None
    while True:
        page = fetch_page(cursor)
        yield from page["items"]
        cursor = page.get("next_cursor")
        if not cursor:
            break


PAGES: dict[str | None, Page] = {
    None: {"items": [1, 2], "next_cursor": "c1"},
    "c1": {"items": [], "next_cursor": "c2"},
    "c2": {"items": [3], "next_cursor": None},
}


def make_fetch(pages: dict[str | None, Page], calls: list[str | None]) -> Callable[[str | None], Page]:
    def fetch_page(cursor: str | None) -> Page:
        calls.append(cursor)
        return pages[cursor]

    return fetch_page


def test_reads_all_pages_in_order() -> None:
    """1 ページ目は None で取り、next_cursor が偽値になるページで終わる。空ページは飛ばす。"""
    calls: list[str | None] = []
    assert list(paginate(make_fetch(PAGES, calls))) == [1, 2, 3]
    assert calls == [None, "c1", "c2"]


@pytest.mark.parametrize("last_page", [{"items": [9], "next_cursor": None}, {"items": [9], "next_cursor": ""}, {"items": [9]}])
def test_falsy_cursor_terminates(last_page: Page) -> None:
    """None / 空文字 / キー無しはすべて終了。"""
    calls: list[str | None] = []
    assert list(paginate(make_fetch({None: last_page}, calls))) == [9]
    assert calls == [None]


def test_is_lazy_and_fetches_next_page_after_consuming_items() -> None:
    """呼んだだけでは取らず、次のページは前のページを消費し切ったあとに取る。"""
    calls: list[str | None] = []
    gen = paginate(make_fetch(PAGES, calls))
    assert inspect.isgenerator(gen)
    assert calls == []
    assert next(gen) == 1
    assert calls == [None]
    assert next(gen) == 2
    assert calls == [None]
    assert next(gen) == 3
    assert calls == [None, "c1", "c2"]


def test_break_stops_fetching_and_runs_finally() -> None:
    """break で抜けると以降のページは取らず、close() で中の finally が実行される。"""
    calls: list[str | None] = []
    events: list[str] = []

    def fetch_page(cursor: str | None) -> Page:
        calls.append(cursor)
        return {"items": [1, 2, 3], "next_cursor": "more"}

    def guarded() -> Iterator[Any]:
        try:
            yield from paginate(fetch_page)
        finally:
            events.append("finally")

    gen = guarded()
    for item in gen:
        if item == 2:
            break
    gen.close()
    assert calls == [None]
    assert events == ["finally"]


def test_fetch_error_propagates() -> None:
    """fetch_page の例外はそのまま伝わり、ジェネレータは終了する。"""

    def fetch_page(cursor: str | None) -> Page:
        raise ConnectionError("down")

    gen = paginate(fetch_page)
    with pytest.raises(ConnectionError, match="down"):
        next(gen)
    with pytest.raises(StopIteration):
        next(gen)


def test_exhausted_generator_yields_nothing() -> None:
    """使い切ったジェネレータをもう一度回しても何も出ない。"""
    calls: list[str | None] = []
    gen = paginate(make_fetch(PAGES, calls))
    assert list(gen) == [1, 2, 3]
    assert list(gen) == []
    assert calls == [None, "c1", "c2"]


def test_zero_cursor_is_treated_as_end() -> None:
    """Pitfalls: 0 は偽値なので終了扱いになる。0 が正当なカーソルなら is None で判定する。"""
    pages: dict[Any, Page] = {None: {"items": [1], "next_cursor": 0}, 0: {"items": [2]}}
    calls: list[Any] = []
    assert list(paginate(make_fetch(pages, calls))) == [1]

    def paginate_is_none(fetch_page: Callable[[Any], Page]) -> Iterator[Any]:
        cursor = None
        while True:
            page = fetch_page(cursor)
            yield from page["items"]
            cursor = page.get("next_cursor")
            if cursor is None:
                break

    assert list(paginate_is_none(make_fetch(pages, calls))) == [1, 2]
