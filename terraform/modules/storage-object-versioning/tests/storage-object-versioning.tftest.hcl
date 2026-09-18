mock_provider "aws" {}

# 既定でバージョニング有効・MFA Delete 無効になること
run "versioning_enabled" {
  command = plan
  variables {
    bucket_name = "example-bucket"
  }

  assert {
    condition     = aws_s3_bucket_versioning.this.bucket == "example-bucket"
    error_message = "渡したバケットに設定が付く"
  }
  assert {
    condition     = aws_s3_bucket_versioning.this.versioning_configuration[0].status == "Enabled"
    error_message = "バージョニングは Enabled"
  }
  assert {
    condition     = aws_s3_bucket_versioning.this.versioning_configuration[0].mfa_delete == "Disabled"
    error_message = "MFA Delete は既定で Disabled"
  }
  assert {
    condition     = aws_s3_bucket_versioning.this.mfa == null
    error_message = "MFA Delete 無効のときは mfa を送らない"
  }
  assert {
    condition     = output.bucket_name == "example-bucket" && output.versioning_status == "Enabled" && output.mfa_delete_enabled == false
    error_message = "outputs はバケット名・状態・MFA Delete を返す"
  }
  assert {
    condition     = output.noncurrent_versions_retained_forever == true
    error_message = "lifecycle を併用しない限り非現行バージョンは残り続けることを出力で示す"
  }
}

# MFA Delete を有効にすると mfa が送られること
run "mfa_delete_enabled" {
  command = plan
  variables {
    bucket_name = "example-bucket"
    mfa_delete  = true
    mfa         = "arn:aws:iam::123456789012:mfa/root-account-mfa-device 123456"
  }

  assert {
    condition     = aws_s3_bucket_versioning.this.versioning_configuration[0].mfa_delete == "Enabled"
    error_message = "MFA Delete が Enabled"
  }
  assert {
    condition     = aws_s3_bucket_versioning.this.mfa == var.mfa
    error_message = "mfa がリクエストに載る"
  }
  assert {
    condition     = output.mfa_delete_enabled == true
    error_message = "mfa_delete_enabled 出力が true"
  }
}

# MFA Delete を有効にするのに mfa が無い指定は弾くこと
run "rejects_mfa_delete_without_mfa" {
  command = plan
  variables {
    bucket_name = "example-bucket"
    mfa_delete  = true
  }
  expect_failures = [aws_s3_bucket_versioning.this]
}
