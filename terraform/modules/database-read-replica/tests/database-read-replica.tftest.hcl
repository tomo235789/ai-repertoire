mock_provider "aws" {}

variables {
  identifier             = "example-db-ro"
  replicate_source_db    = "example-db"
  vpc_security_group_ids = ["sg-0123456789abcdef0"]
  tags                   = { env = "example" }
}

run "same_region_replica" {
  command = plan
  assert {
    condition     = aws_db_instance.this.replicate_source_db == "example-db"
    error_message = "複製元は variable のとおり"
  }
  assert {
    condition     = aws_db_instance.this.publicly_accessible == false
    error_message = "publicly_accessible は常に false"
  }
  assert {
    condition     = aws_db_instance.this.backup_retention_period == 0
    error_message = "レプリカ自身のバックアップは既定で 0（元で取る）"
  }
  assert {
    condition     = aws_db_instance.this.skip_final_snapshot == true
    error_message = "レプリカは最終スナップショットを取れないので skip"
  }
  assert {
    condition     = aws_db_instance.this.auto_minor_version_upgrade == true
    error_message = "マイナーバージョンは自動更新"
  }
  assert {
    condition     = var.kms_key_id == null && var.db_subnet_group_name == null
    error_message = "同一リージョンでは KMS とサブネットグループを省略できる（元から引き継ぐ）"
  }
  assert {
    condition     = aws_db_instance.this.tags == tomap({ env = "example" })
    error_message = "tags がリソースに付く"
  }
}

run "cross_region_replica" {
  command = plan
  variables {
    replicate_source_db     = "arn:aws:rds:us-east-1:123456789012:db:example-db"
    kms_key_id              = "arn:aws:kms:ap-northeast-1:123456789012:key/11111111-2222-3333-4444-555555555555"
    db_subnet_group_name    = "example-private-tokyo"
    instance_class          = "db.r6g.large"
    backup_retention_period = 3
  }
  assert {
    condition     = aws_db_instance.this.kms_key_id == var.kms_key_id
    error_message = "クロスリージョンでは複製先の KMS キーを使う"
  }
  assert {
    condition     = aws_db_instance.this.db_subnet_group_name == "example-private-tokyo"
    error_message = "クロスリージョンでは複製先のサブネットグループを使う"
  }
  assert {
    condition     = aws_db_instance.this.instance_class == "db.r6g.large" && aws_db_instance.this.backup_retention_period == 3
    error_message = "インスタンスクラスと保持日数は variable で変えられる"
  }
}

run "rejects_cross_region_without_kms" {
  command = plan
  variables {
    replicate_source_db  = "arn:aws:rds:us-east-1:123456789012:db:example-db"
    db_subnet_group_name = "example-private-tokyo"
  }
  expect_failures = [var.kms_key_id]
}

run "rejects_cross_region_without_subnet_group" {
  command = plan
  variables {
    replicate_source_db = "arn:aws:rds:us-east-1:123456789012:db:example-db"
    kms_key_id          = "arn:aws:kms:ap-northeast-1:123456789012:key/11111111-2222-3333-4444-555555555555"
  }
  expect_failures = [var.db_subnet_group_name]
}

run "rejects_non_arn_kms_key" {
  command = plan
  variables {
    kms_key_id = "alias/example"
  }
  expect_failures = [var.kms_key_id]
}

run "rejects_retention_over_35" {
  command = plan
  variables {
    backup_retention_period = 36
  }
  expect_failures = [var.backup_retention_period]
}

run "rejects_invalid_identifier" {
  command = plan
  variables {
    identifier = "Example-RO"
  }
  expect_failures = [var.identifier]
}
