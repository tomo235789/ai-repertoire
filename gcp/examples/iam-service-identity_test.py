"""カード iam-service-identity の Contract を検証するテスト"""

import copy
import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("iam-service-identity.py")
    spec = importlib.util.spec_from_file_location("iam_service_identity", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


service_identity_config = _load().service_identity_config

VIEWER = "roles/storage.objectViewer"


def _cfg(**kw):
    return service_identity_config("my-project", "app-runner", [VIEWER], **kw)


def test_email_is_derived():
    """メールアドレスは ID とプロジェクトから決まる"""
    assert _cfg()["email"] == "app-runner@my-project.iam.gserviceaccount.com"


def test_bindings_sorted_and_deduplicated():
    """ロールは重複を除いて名前順。メンバーはこのサービスアカウントだけ"""
    cfg = service_identity_config(
        "my-project", "app-runner", ["roles/logging.logWriter", VIEWER, VIEWER]
    )
    assert [b["role"] for b in cfg["bindings"]] == ["roles/logging.logWriter", VIEWER]
    assert cfg["bindings"][0]["members"] == [
        "serviceAccount:app-runner@my-project.iam.gserviceaccount.com"
    ]


def test_display_name_defaults_to_account_id():
    """表示名を省略すると ID をそのまま使う"""
    assert _cfg()["service_account"]["serviceAccount"]["displayName"] == "app-runner"
    assert _cfg(display_name="アプリ実行用")["service_account"]["serviceAccount"][
        "displayName"
    ] == "アプリ実行用"


def test_workload_identity_binding():
    """Kubernetes の指定があると Workload Identity の紐付けを返す"""
    assert _cfg()["workload_identity_binding"] is None
    binding = _cfg(kubernetes_namespace="prod", kubernetes_service_account="api")[
        "workload_identity_binding"
    ]
    assert binding["role"] == "roles/iam.workloadIdentityUser"
    assert binding["members"] == ["serviceAccount:my-project.svc.id.goog[prod/api]"]
    assert binding["resource"].endswith("/app-runner@my-project.iam.gserviceaccount.com")


def test_workload_identity_needs_both_arguments():
    """名前空間だけ、サービスアカウント名だけでは指定できない"""
    with pytest.raises(ValueError, match="Workload Identity"):
        _cfg(kubernetes_namespace="prod")


def test_privileged_roles_rejected():
    """owner や editor、なりすましにつながるロールは明示許可が要る"""
    for role in (
        "roles/editor",
        "roles/iam.serviceAccountTokenCreator",
        "roles/iam.serviceAccountUser",
        "roles/resourcemanager.projectIamAdmin",
    ):
        with pytest.raises(ValueError, match="広すぎるロール"):
            service_identity_config("my-project", "app-runner", [role])
    cfg = service_identity_config(
        "my-project", "app-runner", ["roles/editor"], allow_privileged_roles=True
    )
    assert cfg["bindings"][0]["role"] == "roles/editor"


def test_empty_workload_identity_names_rejected():
    """名前空間もサービスアカウント名も空にできない"""
    with pytest.raises(ValueError, match="空にできない"):
        _cfg(kubernetes_namespace="", kubernetes_service_account="api")
    with pytest.raises(ValueError, match="空にできない"):
        _cfg(kubernetes_namespace="prod", kubernetes_service_account="")


def test_invalid_inputs():
    """プロジェクト ID・アカウント ID・ロールの不正は ValueError"""
    with pytest.raises(ValueError):
        service_identity_config("My-Project", "app-runner", [VIEWER])
    with pytest.raises(ValueError):
        service_identity_config("my-project", "app", [VIEWER])
    with pytest.raises(ValueError):
        service_identity_config("my-project", "app-runner", [])
    with pytest.raises(ValueError):
        service_identity_config("my-project", "app-runner", ["storage.objectViewer"])


def test_pure_and_serializable():
    """引数を変更せず、返り値は JSON にできる"""
    roles = [VIEWER]
    before = copy.deepcopy(roles)
    cfg = service_identity_config("my-project", "app-runner", roles)
    assert roles == before
    assert json.loads(json.dumps(cfg)) == cfg
