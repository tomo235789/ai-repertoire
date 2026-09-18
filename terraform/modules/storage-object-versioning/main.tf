# バケットのオブジェクトをバージョン管理して誤削除・上書きから守る。
# 削除は「削除マーカー」になり、以前のバージョンは非現行バージョンとして残る。

resource "aws_s3_bucket_versioning" "this" {
  bucket = var.bucket_name
  mfa    = var.mfa_delete ? var.mfa : null

  versioning_configuration {
    status     = "Enabled"
    mfa_delete = var.mfa_delete ? "Enabled" : "Disabled"
  }

  lifecycle {
    precondition {
      condition     = !var.mfa_delete || var.mfa != null
      error_message = "mfa_delete = true のときは mfa（デバイスのシリアル番号とコード）を渡すこと。"
    }
  }
}
