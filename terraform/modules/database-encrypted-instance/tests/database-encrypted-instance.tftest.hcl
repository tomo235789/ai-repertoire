mock_provider "aws" {}

variables {
  identifier             = "example-db"
  engine_version         = "16"
  db_name                = "app"
  db_subnet_group_name   = "example-private"
  vpc_security_group_ids = ["sg-0123456789abcdef0"]
  tags                   = { env = "example" }
}

run "encrypted_with_customer_key" {
  command = plan
  variables {
    kms_key_id = "arn:aws:kms:us-east-1:123456789012:key/11111111-2222-3333-4444-555555555555"
  }
  assert {
    condition     = aws_db_instance.this.storage_encrypted == true
    error_message = "storage_encrypted は常に true"
  }
  assert {
    condition     = aws_db_instance.this.kms_key_id == var.kms_key_id && aws_db_instance.this.master_user_secret_kms_key_id == var.kms_key_id && aws_db_instance.this.performance_insights_kms_key_id == var.kms_key_id
    error_message = "ストレージ・マスターパスワード・Performance Insights が同じ KMS キーで暗号化される"
  }
  assert {
    condition     = aws_db_instance.this.publicly_accessible == false
    error_message = "publicly_accessible は常に false"
  }
  assert {
    condition     = aws_db_instance.this.manage_master_user_password == true && aws_db_instance.this.password == null
    error_message = "パスワードは Secrets Manager が管理し、Terraform には書かない"
  }
  assert {
    condition     = aws_db_instance.this.engine == "postgres" && aws_db_instance.this.engine_version == "16"
    error_message = "エンジンは PostgreSQL"
  }
  assert {
    condition     = aws_db_instance.this.auto_minor_version_upgrade == true
    error_message = "マイナーバージョンは自動更新"
  }
  assert {
    condition     = aws_db_instance.this.performance_insights_enabled == true && aws_db_instance.this.performance_insights_retention_period == 7
    error_message = "Performance Insights は有効、既定の保持は 7 日"
  }
  assert {
    condition     = aws_db_instance.this.deletion_protection == true
    error_message = "削除保護は既定で有効"
  }
  assert {
    condition     = aws_db_instance.this.skip_final_snapshot == false && aws_db_instance.this.final_snapshot_identifier == "example-db-final" && aws_db_instance.this.copy_tags_to_snapshot == true
    error_message = "削除時に最終スナップショット <identifier>-final を残し、タグを引き継ぐ"
  }
  assert {
    condition     = aws_db_instance.this.db_subnet_group_name == "example-private" && aws_db_instance.this.vpc_security_group_ids == toset(["sg-0123456789abcdef0"])
    error_message = "サブネットグループと SG は variable のものを使う"
  }
  assert {
    condition     = aws_db_instance.this.tags == tomap({ env = "example" })
    error_message = "tags がリソースに付く"
  }
}

run "encrypted_with_aws_managed_key" {
  command = plan
  assert {
    condition     = aws_db_instance.this.storage_encrypted == true && var.kms_key_id == null
    error_message = "KMS を渡さなくても暗号化は有効（AWS 管理キー aws/rds が選ばれる）"
  }
}

run "deletion_protection_can_be_disabled" {
  command = plan
  variables {
    deletion_protection = false
  }
  assert {
    condition     = aws_db_instance.this.deletion_protection == false
    error_message = "deletion_protection は variable で切れる"
  }
}

run "rejects_non_arn_kms_key" {
  command = plan
  variables {
    kms_key_id = "alias/example"
  }
  expect_failures = [var.kms_key_id]
}

run "rejects_invalid_identifier" {
  command = plan
  variables {
    identifier = "Example_DB"
  }
  expect_failures = [var.identifier]
}

run "rejects_invalid_pi_retention" {
  command = plan
  variables {
    performance_insights_retention_period = 30
  }
  expect_failures = [var.performance_insights_retention_period]
}

run "rejects_empty_security_groups" {
  command = plan
  variables {
    vpc_security_group_ids = []
  }
  expect_failures = [var.vpc_security_group_ids]
}
