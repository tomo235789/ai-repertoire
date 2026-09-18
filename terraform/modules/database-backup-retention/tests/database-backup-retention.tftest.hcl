mock_provider "aws" {}

variables {
  identifier                = "example-db"
  engine_version            = "16"
  db_subnet_group_name      = "example-private"
  vpc_security_group_ids    = ["sg-0123456789abcdef0"]
  backup_window             = "18:00-19:00"
  final_snapshot_identifier = "example-db-final"
  tags                      = { env = "example" }
}

run "defaults" {
  command = plan
  assert {
    condition     = aws_db_instance.this.backup_retention_period == 7
    error_message = "自動バックアップの既定は 7 日"
  }
  assert {
    condition     = aws_db_instance.this.backup_window == "18:00-19:00"
    error_message = "バックアップ時間帯は variable のとおり"
  }
  assert {
    condition     = aws_db_instance.this.copy_tags_to_snapshot == true
    error_message = "既定でタグをスナップショットにコピーする"
  }
  assert {
    condition     = aws_db_instance.this.delete_automated_backups == false
    error_message = "既定で削除後も自動バックアップを保持期間まで残す"
  }
  assert {
    condition     = aws_db_instance.this.skip_final_snapshot == false && aws_db_instance.this.final_snapshot_identifier == "example-db-final"
    error_message = "削除時は必ず最終スナップショットを取る"
  }
  assert {
    condition     = aws_db_instance.this.storage_encrypted == true && aws_db_instance.this.publicly_accessible == false && aws_db_instance.this.manage_master_user_password == true
    error_message = "最小構成でも暗号化・非公開・パスワードは Secrets Manager 管理"
  }
  assert {
    condition     = aws_db_instance.this.tags == tomap({ env = "example" })
    error_message = "tags がリソースに付く"
  }
}

run "max_retention" {
  command = plan
  variables {
    backup_retention_period  = 35
    delete_automated_backups = true
    copy_tags_to_snapshot    = false
  }
  assert {
    condition     = aws_db_instance.this.backup_retention_period == 35
    error_message = "上限 35 日を受け付ける"
  }
  assert {
    condition     = aws_db_instance.this.delete_automated_backups == true && aws_db_instance.this.copy_tags_to_snapshot == false
    error_message = "delete_automated_backups / copy_tags_to_snapshot は variable で切り替わる"
  }
}

run "rejects_zero_retention" {
  command = plan
  variables {
    backup_retention_period = 0
  }
  expect_failures = [var.backup_retention_period]
}

run "rejects_retention_over_35" {
  command = plan
  variables {
    backup_retention_period = 36
  }
  expect_failures = [var.backup_retention_period]
}

run "rejects_malformed_window" {
  command = plan
  variables {
    backup_window = "3:00-4:00"
  }
  expect_failures = [var.backup_window]
}

run "rejects_unsupported_engine" {
  command = plan
  variables {
    engine = "oracle-ee"
  }
  expect_failures = [var.engine]
}

run "rejects_invalid_snapshot_name" {
  command = plan
  variables {
    final_snapshot_identifier = "example_final"
  }
  expect_failures = [var.final_snapshot_identifier]
}
