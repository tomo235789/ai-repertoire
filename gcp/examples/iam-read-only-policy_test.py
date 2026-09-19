"""カード iam-read-only-policy の Contract を検証するテスト"""

import copy
import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("iam-read-only-policy.py")
    spec = importlib.util.spec_from_file_location("iam_read_only_policy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


read_only_policy = _load().read_only_policy

SA = "serviceAccount:app@my-project.iam.gserviceaccount.com"
USER = "user:analyst@example.com"


def test_version_and_sorted_bindings():
    """version は 3。バインディングはロール順、メンバーは名前順"""
    policy = read_only_policy(
        {"roles/storage.objectViewer": [USER, SA], "roles/bigquery.dataViewer": [USER]}
    )
    assert policy["version"] == 3
    assert [b["role"] for b in policy["bindings"]] == [
        "roles/bigquery.dataViewer",
        "roles/storage.objectViewer",
    ]
    assert policy["bindings"][1]["members"] == sorted([USER, SA])


def test_duplicated_members_collapse():
    """同じメンバーを 2 度書いても 1 件になる"""
    policy = read_only_policy({"roles/storage.objectViewer": [SA, SA]})
    assert policy["bindings"][0]["members"] == [SA]


def test_etag_is_opt_in():
    """etag は渡したときだけ入る"""
    assert "etag" not in read_only_policy({"roles/storage.objectViewer": [SA]})
    policy = read_only_policy({"roles/storage.objectViewer": [SA]}, etag="BwX")
    assert policy["etag"] == "BwX"


def test_condition_applies_to_all_bindings():
    """条件は全バインディングに付く"""
    policy = read_only_policy(
        {"roles/storage.objectViewer": [SA], "roles/bigquery.dataViewer": [SA]},
        condition_expression='resource.name.startsWith("projects/_/buckets/example-bucket")',
        condition_title="example-bucket のみ",
    )
    assert all("condition" in b for b in policy["bindings"])
    assert policy["bindings"][0]["condition"]["title"] == "example-bucket のみ"


def test_condition_needs_title():
    """条件式と名前は両方揃える"""
    with pytest.raises(ValueError, match="条件には"):
        read_only_policy({"roles/storage.objectViewer": [SA]}, condition_expression="true")


def test_public_members_rejected():
    """allUsers と allAuthenticatedUsers には付与しない"""
    for member in ("allUsers", "allAuthenticatedUsers"):
        with pytest.raises(ValueError, match="公開メンバー"):
            read_only_policy({"roles/storage.objectViewer": [member]})


def test_overbroad_roles_rejected():
    """editor や owner、閲覧者でない事前定義ロールは弾く"""
    with pytest.raises(ValueError, match="含められない"):
        read_only_policy({"roles/editor": [SA]})
    with pytest.raises(ValueError, match="閲覧者ロール"):
        read_only_policy({"roles/storage.objectAdmin": [SA]})
    # カスタムロールは中身を検証できないので、明示的に許可したときだけ通す
    with pytest.raises(ValueError, match="カスタムロール"):
        read_only_policy({"projects/my-project/roles/objectLister": [SA]})
    policy = read_only_policy(
        {"projects/my-project/roles/objectLister": [SA]}, allow_custom_roles=True
    )
    assert policy["bindings"][0]["role"] == "projects/my-project/roles/objectLister"


def test_invalid_inputs():
    """空のバインディング、メンバーの形式違いは ValueError"""
    with pytest.raises(ValueError):
        read_only_policy({})
    with pytest.raises(ValueError):
        read_only_policy({"roles/storage.objectViewer": []})
    with pytest.raises(ValueError):
        read_only_policy({"roles/storage.objectViewer": ["analyst@example.com"]})


def test_pure_and_serializable():
    """引数を変更せず、返り値は JSON にできる"""
    bindings = {"roles/storage.objectViewer": [SA]}
    before = copy.deepcopy(bindings)
    policy = read_only_policy(bindings)
    assert bindings == before
    assert json.loads(json.dumps(policy)) == policy
