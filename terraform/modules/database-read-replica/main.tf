# 読み取り負荷を分散するリードレプリカ。
# engine / storage / username は複製元から引き継ぐので指定しない。
resource "aws_db_instance" "this" {
  identifier          = var.identifier
  replicate_source_db = var.replicate_source_db
  instance_class      = var.instance_class

  # 暗号化: 元が暗号化済みならレプリカも暗号化される。クロスリージョンは複製先の鍵を明示する
  kms_key_id = var.kms_key_id

  # ネットワーク: 公開アクセスは常に禁止。サブネットグループは同一リージョンなら元と同じ
  db_subnet_group_name   = var.db_subnet_group_name
  vpc_security_group_ids = var.vpc_security_group_ids
  publicly_accessible    = false
  multi_az               = var.multi_az

  # 運用: レプリカのバックアップは既定で無効（元で取る）。レプリカは最終スナップショットを取れない
  backup_retention_period    = var.backup_retention_period
  auto_minor_version_upgrade = true
  skip_final_snapshot        = true
  copy_tags_to_snapshot      = true

  tags = var.tags
}
