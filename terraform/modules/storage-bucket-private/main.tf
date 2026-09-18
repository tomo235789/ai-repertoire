# 公開アクセスを禁止したオブジェクトストレージのバケットを作る。
# 公開アクセスブロック・保存時暗号化・ACL 無効化・TLS 必須のバケットポリシーを既定にする。

locals {
  use_kms = var.kms_key_arn != null

  # 通信時暗号化: TLS 以外（aws:SecureTransport = false）のリクエストをすべて拒否する
  bucket_policy = {
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.this.arn,
          "${aws_s3_bucket.this.arn}/*",
        ]
        Condition = {
          Bool = { "aws:SecureTransport" = "false" }
        }
      },
    ]
  }
}

resource "aws_s3_bucket" "this" {
  bucket        = var.name
  force_destroy = var.force_destroy
  tags          = var.tags
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ACL を無効化し、オブジェクトの所有者を常にバケット所有者にする
resource "aws_s3_bucket_ownership_controls" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = local.use_kms ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_arn
    }
    # KMS のときは Bucket Key で KMS 呼び出し回数を減らす
    bucket_key_enabled = local.use_kms
  }
}

resource "aws_s3_bucket_policy" "this" {
  bucket = aws_s3_bucket.this.id
  policy = jsonencode(local.bucket_policy)

  # 公開アクセスブロックより先にポリシーを付けると競合するので順序を固定する
  depends_on = [aws_s3_bucket_public_access_block.this]
}
