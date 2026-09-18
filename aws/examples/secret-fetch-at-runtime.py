"""カード secret-fetch-at-runtime: シークレットの作成と、読み取りを特定プリンシパルに限定するリソースポリシー

secretsmanager.create_secret の kwargs と、put_resource_policy に渡す ResourcePolicy（dict）を返す。
値（SecretString / SecretBinary）はこの関数では扱わない。実行時に GetSecretValue で取得する前提。
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

# Secrets Manager の Name に使える文字。1〜512 文字
_NAME_RE = re.compile(r"^[A-Za-z0-9/_+=.@-]{1,512}$")
_IAM_ARN_RE = re.compile(r"^arn:aws(?:-[a-z]+)?:iam::\d{12}:(?:root|user/|role/|group/)")


def secret_and_read_policy(
    name: str,
    kms_key_id: str | None = None,
    reader_principal_arns: Sequence[str] = (),
    *,
    description: str | None = None,
    tags: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """シークレット作成の kwargs と、GetSecretValue を reader_principal_arns だけに許すリソースポリシーを返す。

    :param name: シークレット名（`app/prod/db` のような階層名）
    :param kms_key_id: 暗号化に使う CMK。None なら AWS 管理キー aws/secretsmanager
    :param reader_principal_arns: GetSecretValue を許可する IAM プリンシパルの ARN。1 つ以上必須
    :returns: {"create_secret": create_secret の kwargs, "read_policy": put_resource_policy の ResourcePolicy}
    """
    if not _NAME_RE.match(name):
        raise ValueError(f"シークレット名が不正: {name!r}（英数字と /_+=.@- で 1〜512 文字）")
    readers = list(reader_principal_arns)
    if not readers:
        raise ValueError("reader_principal_arns は 1 つ以上必要。空だと誰も読めないポリシーになる")
    if len(set(readers)) != len(readers):
        raise ValueError("reader_principal_arns に重複がある")
    for arn in readers:
        if "*" in arn or not _IAM_ARN_RE.match(arn):
            raise ValueError(f"IAM プリンシパルの ARN ではない（ワイルドカード不可）: {arn!r}")

    create_secret: dict[str, Any] = {"Name": name}
    if description:
        create_secret["Description"] = description
    if kms_key_id:
        create_secret["KmsKeyId"] = kms_key_id
    if tags:
        create_secret["Tags"] = [{"Key": k, "Value": v} for k, v in sorted(tags.items())]

    read_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowReadersGetSecretValue",
                "Effect": "Allow",
                "Principal": {"AWS": readers},
                "Action": "secretsmanager:GetSecretValue",
                "Resource": "*",
            },
            {
                "Sid": "DenyGetSecretValueToOthers",
                "Effect": "Deny",
                "Principal": {"AWS": "*"},
                "Action": "secretsmanager:GetSecretValue",
                "Resource": "*",
                "Condition": {"ArnNotEquals": {"aws:PrincipalArn": readers}},
            },
        ],
    }
    return {"create_secret": create_secret, "read_policy": read_policy}
