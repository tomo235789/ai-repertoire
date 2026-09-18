"""カード secret-rotation: Lambda によるシークレットの定期ローテーション設定

secretsmanager.rotate_secret の kwargs を返す。スケジュールは rate 式で表す。
"""

from __future__ import annotations

import re
from typing import Any

_LAMBDA_ARN_RE = re.compile(r"^arn:aws(?:-[a-z]+)?:lambda:[a-z0-9-]+:\d{12}:function:[A-Za-z0-9_-]+(?::[A-Za-z0-9_$-]+)?$")

MIN_DAYS = 1
MAX_DAYS = 365


def rotation_config(
    secret_id: str,
    rotation_lambda_arn: str,
    days: int,
    rotate_immediately: bool = False,
) -> dict[str, Any]:
    """rotate_secret の kwargs を返す。

    :param secret_id: シークレットの名前か ARN
    :param rotation_lambda_arn: ローテーション Lambda の関数 ARN
    :param days: ローテーション間隔（日）。1〜365
    :param rotate_immediately: True なら設定と同時に 1 回ローテーションする。既定は False（次回スケジュールまで待つ）
    """
    if not secret_id:
        raise ValueError("secret_id は必須")
    if not _LAMBDA_ARN_RE.match(rotation_lambda_arn):
        raise ValueError(f"Lambda の関数 ARN ではない: {rotation_lambda_arn!r}")
    if isinstance(days, bool) or not isinstance(days, int):
        raise TypeError("days は int")
    if not MIN_DAYS <= days <= MAX_DAYS:
        raise ValueError(f"days は {MIN_DAYS}〜{MAX_DAYS} の範囲（実際: {days}）")

    unit = "day" if days == 1 else "days"
    return {
        "SecretId": secret_id,
        "RotationLambdaARN": rotation_lambda_arn,
        "RotationRules": {"ScheduleExpression": f"rate({days} {unit})"},
        "RotateImmediately": bool(rotate_immediately),
    }
