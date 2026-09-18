# 保存時暗号化を有効にした PostgreSQL インスタンス。
# パスワードは Secrets Manager が生成・保管し、Terraform の state と設定には残さない。
resource "aws_db_instance" "this" {
  identifier        = var.identifier
  engine            = "postgres"
  engine_version    = var.engine_version
  instance_class    = var.instance_class
  allocated_storage = var.allocated_storage
  storage_type      = "gp3"
  db_name           = var.db_name
  username          = var.master_username

  # 暗号化: ストレージ・マスターパスワード・Performance Insights の 3 か所を同じ鍵で
  storage_encrypted                     = true
  kms_key_id                            = var.kms_key_id
  manage_master_user_password           = true
  master_user_secret_kms_key_id         = var.kms_key_id
  performance_insights_enabled          = true
  performance_insights_kms_key_id       = var.kms_key_id
  performance_insights_retention_period = var.performance_insights_retention_period

  # ネットワーク: プライベートサブネット + SG のみ。公開アクセスは常に禁止
  db_subnet_group_name   = var.db_subnet_group_name
  vpc_security_group_ids = var.vpc_security_group_ids
  publicly_accessible    = false
  multi_az               = var.multi_az

  # 運用: マイナーバージョン自動更新、削除保護、削除時は最終スナップショットを残す
  auto_minor_version_upgrade = true
  deletion_protection        = var.deletion_protection
  skip_final_snapshot        = false
  final_snapshot_identifier  = "${var.identifier}-final"
  copy_tags_to_snapshot      = true

  tags = var.tags
}
