mock_provider "aws" {
  override_during = plan
  mock_resource "aws_s3_bucket" {
    defaults = {
      arn = "arn:aws:s3:::example-bucket"
      id  = "example-bucket"
    }
  }
}

# 既定（SSE-S3）で公開アクセス禁止・暗号化・所有権・TLS 必須が揃うこと
run "private_bucket_defaults" {
  command = plan
  variables {
    name = "example-bucket"
    tags = { env = "test" }
  }

  assert {
    condition = (
      aws_s3_bucket_public_access_block.this.block_public_acls &&
      aws_s3_bucket_public_access_block.this.block_public_policy &&
      aws_s3_bucket_public_access_block.this.ignore_public_acls &&
      aws_s3_bucket_public_access_block.this.restrict_public_buckets
    )
    error_message = "公開アクセスブロックは 4 項目すべて true でなければならない"
  }
  assert {
    condition     = aws_s3_bucket_ownership_controls.this.rule[0].object_ownership == "BucketOwnerEnforced"
    error_message = "ACL は無効化（BucketOwnerEnforced）されていなければならない"
  }
  assert {
    condition     = tolist(tolist(aws_s3_bucket_server_side_encryption_configuration.this.rule)[0].apply_server_side_encryption_by_default)[0].sse_algorithm == "AES256"
    error_message = "kms_key_arn を渡さないときは SSE-S3（AES256）で暗号化する"
  }
  assert {
    condition     = tolist(aws_s3_bucket_server_side_encryption_configuration.this.rule)[0].bucket_key_enabled == false
    error_message = "SSE-S3 のときは Bucket Key を使わない"
  }
  assert {
    condition = anytrue([
      for s in jsondecode(aws_s3_bucket_policy.this.policy).Statement :
      s.Effect == "Deny" && s.Action == "s3:*" && s.Condition.Bool["aws:SecureTransport"] == "false"
      && contains(s.Resource, "arn:aws:s3:::example-bucket") && contains(s.Resource, "arn:aws:s3:::example-bucket/*")
    ])
    error_message = "バケットポリシーは TLS 以外のアクセスをバケットとオブジェクトの両方で Deny しなければならない"
  }
  assert {
    condition     = aws_s3_bucket.this.tags["env"] == "test"
    error_message = "tags がバケットに付いていなければならない"
  }
  assert {
    condition     = aws_s3_bucket.this.force_destroy == false
    error_message = "force_destroy の既定は false"
  }
  assert {
    condition     = output.bucket_name == "example-bucket" && output.bucket_arn == "arn:aws:s3:::example-bucket" && output.sse_algorithm == "AES256"
    error_message = "outputs はバケット名・ARN・暗号化方式を返す"
  }
}

# KMS キーを渡すと SSE-KMS + Bucket Key になること
run "sse_kms" {
  command = plan
  variables {
    name        = "example-bucket"
    kms_key_arn = "arn:aws:kms:us-east-1:123456789012:key/11111111-2222-3333-4444-555555555555"
  }

  assert {
    condition     = tolist(tolist(aws_s3_bucket_server_side_encryption_configuration.this.rule)[0].apply_server_side_encryption_by_default)[0].sse_algorithm == "aws:kms"
    error_message = "kms_key_arn を渡したときは aws:kms で暗号化する"
  }
  assert {
    condition     = tolist(tolist(aws_s3_bucket_server_side_encryption_configuration.this.rule)[0].apply_server_side_encryption_by_default)[0].kms_master_key_id == var.kms_key_arn
    error_message = "渡した KMS キーが既定の暗号化キーになる"
  }
  assert {
    condition     = tolist(aws_s3_bucket_server_side_encryption_configuration.this.rule)[0].bucket_key_enabled == true
    error_message = "SSE-KMS のときは Bucket Key を有効にする"
  }
  assert {
    condition     = output.sse_algorithm == "aws:kms"
    error_message = "sse_algorithm 出力は aws:kms"
  }
}

# 命名規則に反するバケット名は validation で弾くこと
run "rejects_invalid_name" {
  command = plan
  variables {
    name = "Example_Bucket"
  }
  expect_failures = [var.name]
}

# KMS 以外の ARN は弾くこと
run "rejects_non_kms_arn" {
  command = plan
  variables {
    name        = "example-bucket"
    kms_key_arn = "arn:aws:s3:::not-a-key"
  }
  expect_failures = [var.kms_key_arn]
}
