"""カード compute-serverless-function: 関数アプリの構成を組み立てる純粋関数。

`azure-mgmt-web` の `web_apps.begin_create_or_update` に渡す Site を返す。
接続文字列を作らず、ストレージへの接続はマネージド ID を使う。API は呼ばない。
"""

from __future__ import annotations

import re

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,58}[a-z0-9]$")

# 値が Key Vault 参照でなければならない設定名の語尾
SECRET_NAME_SUFFIXES = ("password", "secret", "token", "apikey", "accesskey", "key")
# 受け付ける参照は SecretUri 形式か VaultName + SecretName 形式のどちらか。
# 金庫名とシークレット名は英数字とハイフンだけ（アンダースコアは使えない）
_VAULT_NAME = r"[a-zA-Z][a-zA-Z0-9-]{1,22}[a-zA-Z0-9]"
_SECRET_NAME = r"[a-zA-Z0-9-]{1,127}"
_SECRET_VERSION = r"[0-9a-f]{32}"
_KEY_VAULT_REFERENCE_RE = re.compile(
    r"^@Microsoft\.KeyVault\("
    rf"(SecretUri=https://{_VAULT_NAME}\.vault\.azure\.net/secrets/"
    rf"{_SECRET_NAME}(/{_SECRET_VERSION})?/?"
    rf"|VaultName={_VAULT_NAME};\s*SecretName={_SECRET_NAME}"
    rf"(;\s*SecretVersion={_SECRET_VERSION})?)"
    r"\)$"
)


def _is_secret_name(key: str) -> bool:
    """区切り文字と大文字小文字を落としてから、秘密用途の名前かを見る"""
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    return normalized.endswith(SECRET_NAME_SUFFIXES)

# ランタイムごとの linuxFxVersion とワーカー名
RUNTIMES: dict[str, tuple[str, str]] = {
    "python3.12": ("Python|3.12", "python"),
    "python3.11": ("Python|3.11", "python"),
    "node20": ("Node|20", "node"),
    "dotnet8": ("DOTNET-ISOLATED|8.0", "dotnet-isolated"),
}


def serverless_function_config(
    name: str,
    runtime: str,
    storage_account_name: str,
    server_farm_id: str,
    *,
    app_insights_connection_string: str | None = None,
    app_settings: dict[str, str] | None = None,
    always_on: bool = False,
) -> dict:
    """イベント駆動で動く関数アプリの構成を返す。

    Args:
        name: 関数アプリ名。英小文字・数字・ハイフンで 3〜60 文字
        runtime: RUNTIMES のキー
        storage_account_name: 実行基盤が使うストレージアカウント名
        server_farm_id: プラン（App Service プラン）の ARM ID
        app_insights_connection_string: 監視の接続文字列
        app_settings: 追加のアプリ設定。秘密の値そのものは入れない
        always_on: 常時起動させるか。従量課金プランでは効かない

    Returns:
        location 抜きの Site（kind / identity / properties を持つ dict）

    Raises:
        ValueError: 名前の形式違い、未知のランタイム、
            秘密用途の名前に Key Vault 参照でない値を入れた場合
    """
    if not _NAME_RE.fullmatch(name):
        raise ValueError(f"関数アプリ名は英小文字・数字・ハイフンで 3〜60 文字: {name!r}")
    if runtime not in RUNTIMES:
        raise ValueError(f"未知のランタイム: {runtime!r}")

    linux_fx_version, worker = RUNTIMES[runtime]
    settings: dict[str, str] = {
        "FUNCTIONS_EXTENSION_VERSION": "~4",
        "FUNCTIONS_WORKER_RUNTIME": worker,
        # 接続文字列ではなくマネージド ID でストレージに接続する
        "AzureWebJobsStorage__accountName": storage_account_name,
        "AzureWebJobsStorage__credential": "managedidentity",
        # 配置済みパッケージを読み取り専用で実行する
        "WEBSITE_RUN_FROM_PACKAGE": "1",
    }
    if app_insights_connection_string is not None:
        settings["APPLICATIONINSIGHTS_CONNECTION_STRING"] = app_insights_connection_string
    for key, value in (app_settings or {}).items():
        if key in settings:
            raise ValueError(f"予約済みのアプリ設定は上書きできない: {key}")
        looks_like_connection_string = (
            "accountkey=" in value.lower() or "sharedaccesskey=" in value.lower()
        )
        if looks_like_connection_string or (
            _is_secret_name(key) and not _KEY_VAULT_REFERENCE_RE.fullmatch(value)
        ):
            raise ValueError(
                f"アプリ設定に秘密値を直接入れない（{key}）。Key Vault 参照を使う"
            )
        settings[key] = value

    return {
        "kind": "functionapp,linux",
        "identity": {"type": "SystemAssigned"},
        "properties": {
            "serverFarmId": server_farm_id,
            "httpsOnly": True,
            "clientCertEnabled": False,
            "siteConfig": {
                "linuxFxVersion": linux_fx_version,
                "minTlsVersion": "1.2",
                "ftpsState": "Disabled",
                "http20Enabled": True,
                "alwaysOn": always_on,
                "appSettings": [
                    {"name": k, "value": v} for k, v in sorted(settings.items())
                ],
            },
        },
    }
