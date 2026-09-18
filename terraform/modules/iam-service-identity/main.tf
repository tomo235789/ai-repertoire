# ワークロード用のサービス ID。IAM ユーザーと長期アクセスキーを作らず、
# サービス principal か OIDC プロバイダから引き受ける一時的な資格情報だけを与える。

locals {
  is_oidc = var.principal_type == "oidc"

  # OIDC の条件キーは "<provider host>:sub" / "<provider host>:aud"（service のときは未使用なので空文字）
  oidc_host = try(element(split("oidc-provider/", var.oidc_provider_arn), 1), "")

  # sub に `*` を含むときは StringLike、含まないときは StringEquals で厳密比較する
  subject_operator = anytrue([for s in var.oidc_subjects : strcontains(s, "*")]) ? "StringLike" : "StringEquals"

  service_statement = {
    Sid       = "AllowServiceAssume"
    Effect    = "Allow"
    Principal = { Service = var.service_principal }
    Action    = "sts:AssumeRole"
  }

  oidc_statement = {
    Sid       = "AllowWebIdentityAssume"
    Effect    = "Allow"
    Principal = { Federated = var.oidc_provider_arn }
    Action    = "sts:AssumeRoleWithWebIdentity"
    Condition = merge(
      {
        StringEquals = merge(
          { "${local.oidc_host}:aud" = var.oidc_audiences },
          local.subject_operator == "StringEquals" ? { "${local.oidc_host}:sub" = var.oidc_subjects } : {},
        )
      },
      local.subject_operator == "StringLike" ? { StringLike = { "${local.oidc_host}:sub" = var.oidc_subjects } } : {},
    )
  }

  # 三項演算子は両辺の object 型が揃わないと使えないので concat で片方だけ残す
  assume_role_policy = {
    Version   = "2012-10-17"
    Statement = concat(local.is_oidc ? [local.oidc_statement] : [], local.is_oidc ? [] : [local.service_statement])
  }
}

resource "aws_iam_role" "this" {
  name                 = var.name
  assume_role_policy   = jsonencode(local.assume_role_policy)
  permissions_boundary = var.permissions_boundary_arn
  max_session_duration = var.max_session_duration
  tags                 = var.tags

  lifecycle {
    precondition {
      condition     = local.is_oidc || var.service_principal != null
      error_message = "principal_type = service のときは service_principal を渡すこと。"
    }
    precondition {
      condition     = !local.is_oidc || (var.oidc_provider_arn != null && length(var.oidc_subjects) > 0)
      error_message = "principal_type = oidc のときは oidc_provider_arn と 1 つ以上の oidc_subjects を渡すこと（sub を絞らないとプロバイダの全トークンが引き受けられる）。"
    }
    precondition {
      condition     = !local.is_oidc || length(var.oidc_audiences) > 0
      error_message = "principal_type = oidc のときは oidc_audiences を 1 つ以上渡すこと。"
    }
  }
}

resource "aws_iam_role_policy_attachment" "this" {
  for_each   = toset(var.policy_arns)
  role       = aws_iam_role.this.name
  policy_arn = each.value
}
