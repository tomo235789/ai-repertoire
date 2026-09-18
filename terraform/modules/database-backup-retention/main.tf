# 自動バックアップと保持期間を設定した DB インスタンス。
# インスタンス自体は最小構成（暗号化・非公開・パスワードは Secrets Manager 管理）で、
# バックアップに関わる 5 つの設定を variable で受ける。
resource "aws_db_instance" "this" {
  identifier        = var.identifier
  engine            = var.engine
  engine_version    = var.engine_version
  instance_class    = var.instance_class
  allocated_storage = var.allocated_storage
  storage_type      = "gp3"

  storage_encrypted           = true
  manage_master_user_password = true
  db_subnet_group_name        = var.db_subnet_group_name
  vpc_security_group_ids      = var.vpc_security_group_ids
  publicly_accessible         = false

  # バックアップ: 自動バックアップ（PITR）+ 削除時の最終スナップショット
  backup_retention_period   = var.backup_retention_period
  backup_window             = var.backup_window
  copy_tags_to_snapshot     = var.copy_tags_to_snapshot
  delete_automated_backups  = var.delete_automated_backups
  skip_final_snapshot       = false
  final_snapshot_identifier = var.final_snapshot_identifier

  tags = var.tags
}
