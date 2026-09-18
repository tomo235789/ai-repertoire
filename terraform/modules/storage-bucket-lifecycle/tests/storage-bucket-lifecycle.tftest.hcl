mock_provider "aws" {}

# 移行・削除・非現行削除・マルチパート中止が 1 規則に揃うこと
run "full_rule" {
  command = plan
  variables {
    bucket_name                        = "example-bucket"
    prefix                             = "logs/"
    transition_days                    = 30
    expiration_days                    = 365
    noncurrent_version_expiration_days = 30
  }

  assert {
    condition     = aws_s3_bucket_lifecycle_configuration.this.bucket == "example-bucket"
    error_message = "渡したバケットに規則が付く"
  }
  assert {
    condition     = length(aws_s3_bucket_lifecycle_configuration.this.rule) == 1 && aws_s3_bucket_lifecycle_configuration.this.rule[0].status == "Enabled"
    error_message = "規則は 1 つで Enabled"
  }
  assert {
    condition     = aws_s3_bucket_lifecycle_configuration.this.rule[0].filter[0].prefix == "logs/"
    error_message = "prefix が filter に反映される"
  }
  assert {
    condition     = tolist(aws_s3_bucket_lifecycle_configuration.this.rule[0].transition)[0].days == 30 && tolist(aws_s3_bucket_lifecycle_configuration.this.rule[0].transition)[0].storage_class == "STANDARD_IA"
    error_message = "transition_days 日後に既定の STANDARD_IA へ移行する"
  }
  assert {
    condition     = aws_s3_bucket_lifecycle_configuration.this.rule[0].expiration[0].days == 365
    error_message = "expiration_days 日後に現行バージョンを削除する"
  }
  assert {
    condition     = aws_s3_bucket_lifecycle_configuration.this.rule[0].noncurrent_version_expiration[0].noncurrent_days == 30
    error_message = "非現行バージョンは noncurrent_version_expiration_days 日後に削除する"
  }
  assert {
    condition     = aws_s3_bucket_lifecycle_configuration.this.rule[0].abort_incomplete_multipart_upload[0].days_after_initiation == 7
    error_message = "未完了マルチパートは既定で 7 日後に中止する"
  }
  assert {
    condition     = output.bucket_name == "example-bucket" && output.rule_id == "retention" && output.rule_status == "Enabled"
    error_message = "outputs はバケット名・規則 ID・状態を返す"
  }
}

# 削除だけの指定では移行・非現行削除ブロックが生成されないこと（バケット全体が対象）
run "expiration_only" {
  command = plan
  variables {
    bucket_name     = "example-bucket"
    expiration_days = 90
  }

  assert {
    condition     = length(aws_s3_bucket_lifecycle_configuration.this.rule[0].transition) == 0 && length(aws_s3_bucket_lifecycle_configuration.this.rule[0].noncurrent_version_expiration) == 0
    error_message = "null の項目はブロックを生成しない"
  }
  assert {
    condition     = aws_s3_bucket_lifecycle_configuration.this.rule[0].filter[0].prefix == ""
    error_message = "prefix 未指定はバケット全体"
  }
}

# 移行より前に削除する規則は弾くこと
run "rejects_expiration_before_transition" {
  command = plan
  variables {
    bucket_name     = "example-bucket"
    transition_days = 90
    expiration_days = 30
  }
  expect_failures = [aws_s3_bucket_lifecycle_configuration.this]
}

# STANDARD_IA へ 30 日未満で移行する規則は弾くこと
run "rejects_ia_transition_under_30_days" {
  command = plan
  variables {
    bucket_name     = "example-bucket"
    transition_days = 7
  }
  expect_failures = [aws_s3_bucket_lifecycle_configuration.this]
}

# GLACIER_IR なら 30 日未満でも許すこと
run "allows_short_glacier_ir_transition" {
  command = plan
  variables {
    bucket_name              = "example-bucket"
    transition_days          = 1
    transition_storage_class = "GLACIER_IR"
  }
  assert {
    condition     = tolist(aws_s3_bucket_lifecycle_configuration.this.rule[0].transition)[0].storage_class == "GLACIER_IR"
    error_message = "GLACIER_IR への移行"
  }
}

# 負数・小数の日数は弾くこと
run "rejects_negative_days" {
  command = plan
  variables {
    bucket_name     = "example-bucket"
    expiration_days = -1
  }
  expect_failures = [var.expiration_days]
}

# 未対応のストレージクラスは弾くこと
run "rejects_unknown_storage_class" {
  command = plan
  variables {
    bucket_name              = "example-bucket"
    transition_days          = 30
    transition_storage_class = "REDUCED_REDUNDANCY"
  }
  expect_failures = [var.transition_storage_class]
}
