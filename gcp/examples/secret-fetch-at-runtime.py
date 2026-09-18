"""カード secret-fetch-at-runtime: 秘密を実行時に Secret Manager から取る設定を
組み立てる純粋関数。

Cloud Run の `secretKeyRef` と、読み取りに必要な IAM バインディングを返す。
秘密の値そのものは扱わず、API も呼ばない。
"""

from __future__ import annotations

import re

_SECRET_RE = re.compile(r"^[a-zA-Z0-9_-]{1,255}$")
_ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_PROJECT_RE = re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")

SECRET_ACCESSOR_ROLE = "roles/secretmanager.secretAccessor"


def secret_version_name(project_id: str, secret_id: str, version: str = "latest") -> str:
    """シークレットのバージョンの完全名を返す。

    Raises:
        ValueError: プロジェクト ID やシークレット名の形式違い、
            バージョンが "latest" でも正の整数でもない場合
    """
    if not _PROJECT_RE.match(project_id):
        raise ValueError(f"プロジェクト ID の形式が不正: {project_id!r}")
    if not _SECRET_RE.match(secret_id):
        raise ValueError(f"シークレット名の形式が不正: {secret_id!r}")
    if version != "latest" and not (version.isdigit() and int(version) > 0):
        raise ValueError(f"バージョンは 'latest' か正の整数: {version!r}")
    return f"projects/{project_id}/secrets/{secret_id}/versions/{version}"


def runtime_secret_config(
    project_id: str,
    secrets: dict[str, str],
    service_account: str,
    *,
    pin_versions: dict[str, str] | None = None,
) -> dict:
    """環境変数への注入設定と、読み取りの IAM バインディングを返す。

    Args:
        project_id: プロジェクト ID
        secrets: 環境変数名 -> シークレット名
        service_account: 読み取るサービスアカウントのメールアドレス
        pin_versions: 環境変数名 -> 固定するバージョン

    Returns:
        env（secretKeyRef の列）と iam_bindings（シークレットごと）を持つ dict

    Raises:
        ValueError: secrets が空、環境変数名が大文字とアンダースコア以外、
            サービスアカウントがメールアドレスでない、
            pin_versions に secrets に無いキーがある場合
    """
    if not secrets:
        raise ValueError("secrets は 1 件以上必要")
    if "@" not in service_account:
        raise ValueError(f"サービスアカウントはメールアドレスで指定する: {service_account!r}")
    pin_versions = dict(pin_versions or {})
    unknown = set(pin_versions) - set(secrets)
    if unknown:
        raise ValueError(f"secrets に無い環境変数のバージョンは固定できない: {sorted(unknown)}")

    env: list[dict] = []
    iam_bindings: list[dict] = []
    member = f"serviceAccount:{service_account}"
    for env_name, secret_id in sorted(secrets.items()):
        if not _ENV_RE.match(env_name):
            raise ValueError(f"環境変数名は大文字とアンダースコア: {env_name!r}")
        version = pin_versions.get(env_name, "latest")
        # 形式の検査はここで一度だけ行う
        secret_version_name(project_id, secret_id, version)
        env.append(
            {
                "name": env_name,
                "value_source": {
                    "secret_key_ref": {"secret": secret_id, "version": version}
                },
            }
        )
        iam_bindings.append(
            {
                "resource": f"projects/{project_id}/secrets/{secret_id}",
                "role": SECRET_ACCESSOR_ROLE,
                "members": [member],
            }
        )
    return {"env": env, "iam_bindings": iam_bindings}
