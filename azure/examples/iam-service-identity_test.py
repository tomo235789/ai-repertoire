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


_mod = _load()
service_identity_config = _mod.service_identity_config
BUILT_IN_ROLES = _mod.BUILT_IN_ROLES

PRINCIPAL = "11111111-2222-3333-4444-555555555555"
SCOPE = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"


def test_system_assigned_default():
    """既定はシステム割り当て ID に Reader を割り当てる"""
    cfg = service_identity_config(PRINCIPAL, SCOPE)
    assert cfg["identity"] == {"type": "SystemAssigned"}
    assert cfg["role_name"] == "Reader"
    assert cfg["assignment"]["parameters"]["properties"]["roleDefinitionId"].endswith(
        BUILT_IN_ROLES["Reader"]
    )
    assert cfg["assignment"]["parameters"]["properties"]["principalType"] == "ServicePrincipal"


def test_user_assigned_identity():
    """ユーザー割り当て ID は userAssignedIdentities に ARM ID をキーとして入る"""
    uami = (
        "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
        "/providers/Microsoft.ManagedIdentity/userAssignedIdentities/example-mi"
    )
    cfg = service_identity_config(PRINCIPAL, SCOPE, user_assigned_identity_id=uami)
    assert cfg["identity"]["type"] == "UserAssigned"
    assert cfg["identity"]["userAssignedIdentities"] == {uami: {}}


def test_role_definition_id_uses_subscription_scope():
    """割り当て先がリソースグループでも、ロール定義 ID はサブスクリプション配下"""
    cfg = service_identity_config(PRINCIPAL, SCOPE, role_name="Storage Blob Data Reader")
    assert cfg["assignment"]["parameters"]["properties"]["roleDefinitionId"] == (
        "/subscriptions/00000000-0000-0000-0000-000000000000"
        "/providers/Microsoft.Authorization/roleDefinitions/"
        "2a2b9908-6ea1-4ae2-8e65-a410df84e7d1"
    )
    # 割り当て先のスコープはリソースグループのまま
    assert cfg["assignment"]["scope"] == SCOPE


def test_assignment_name_is_deterministic():
    """同じ入力なら割り当て名も同じ（再実行しても重複した割り当てを作らない）"""
    a = service_identity_config(PRINCIPAL, SCOPE)
    b = service_identity_config(PRINCIPAL, SCOPE)
    assert a["assignment"]["role_assignment_name"] == b["assignment"]["role_assignment_name"]
    c = service_identity_config(PRINCIPAL, SCOPE, role_name="Contributor")
    assert c["assignment"]["role_assignment_name"] != a["assignment"]["role_assignment_name"]


def test_privileged_role_rejected():
    """Owner / User Access Administrator は明示許可なしでは弾く"""
    with pytest.raises(ValueError, match="allow_privileged_role"):
        service_identity_config(PRINCIPAL, SCOPE, role_name="Owner")
    cfg = service_identity_config(
        PRINCIPAL, SCOPE, role_name="Owner", allow_privileged_role=True
    )
    assert cfg["role_name"] == "Owner"


def test_invalid_inputs():
    """GUID でない principal_id、scope の形式違い、未知のロールは ValueError"""
    with pytest.raises(ValueError):
        service_identity_config("not-a-guid", SCOPE)
    with pytest.raises(ValueError):
        service_identity_config(PRINCIPAL, "example-rg")
    with pytest.raises(ValueError):
        service_identity_config(PRINCIPAL, SCOPE, role_name="Superuser")


def test_pure_and_serializable():
    """入力を変更せず、返り値は JSON にできる"""
    scope = SCOPE
    before = copy.deepcopy(scope)
    cfg = service_identity_config(PRINCIPAL, scope)
    assert scope == before
    assert json.loads(json.dumps(cfg)) == cfg
