mock_provider "aws" {
  override_during = plan
  mock_resource "aws_cloudfront_distribution" {
    defaults = {
      arn         = "arn:aws:cloudfront::123456789012:distribution/E1EXAMPLE0001"
      id          = "E1EXAMPLE0001"
      domain_name = "d111111abcdef8.cloudfront.net"
    }
  }
  mock_resource "aws_cloudfront_origin_access_control" {
    defaults = {
      id = "E2EXAMPLEOAC0"
    }
  }
}

variables {
  bucket_name                 = "example-bucket"
  bucket_regional_domain_name = "example-bucket.s3.us-east-1.amazonaws.com"
  certificate_arn             = "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"
  aliases                     = ["static.example.com"]
  tags                        = { env = "test" }
}

# 既定で HTTPS 強制・TLS 1.2 以上・OAC 経由・非公開バケットが揃う
run "https_and_oac_defaults" {
  command = plan

  assert {
    condition     = aws_cloudfront_distribution.this.default_cache_behavior[0].viewer_protocol_policy == "redirect-to-https"
    error_message = "HTTP は HTTPS へリダイレクトすること"
  }

  assert {
    condition     = aws_cloudfront_distribution.this.viewer_certificate[0].minimum_protocol_version == "TLSv1.2_2021"
    error_message = "TLS は 1.2 以上を要求すること"
  }

  assert {
    condition     = aws_cloudfront_distribution.this.viewer_certificate[0].ssl_support_method == "sni-only"
    error_message = "SNI で証明書を提示すること"
  }

  assert {
    condition     = aws_cloudfront_origin_access_control.this.signing_behavior == "always"
    error_message = "OAC は常に署名すること（バケットを公開しない）"
  }

  assert {
    condition     = aws_cloudfront_origin_access_control.this.origin_access_control_origin_type == "s3"
    error_message = "OAC の origin type は s3 にすること"
  }

  assert {
    condition     = aws_cloudfront_distribution.this.default_root_object == "index.html"
    error_message = "既定のルートオブジェクトは index.html"
  }

  assert {
    condition     = aws_cloudfront_distribution.this.price_class == "PriceClass_100"
    error_message = "price_class の既定は PriceClass_100"
  }

  assert {
    condition     = aws_cloudfront_distribution.this.tags["env"] == "test"
    error_message = "tags を配信に付けること"
  }
}

# バケットポリシーは「この配信からの GetObject」だけを許可する
run "bucket_policy_limits_to_this_distribution" {
  command = plan

  assert {
    condition     = length(data.aws_iam_policy_document.bucket.statement) == 1
    error_message = "Statement は 1 つだけにすること"
  }

  assert {
    condition     = tolist(data.aws_iam_policy_document.bucket.statement[0].actions) == tolist(["s3:GetObject"])
    error_message = "許可する action は s3:GetObject だけにすること"
  }

  assert {
    condition     = tolist(data.aws_iam_policy_document.bucket.statement[0].resources) == tolist(["arn:aws:s3:::example-bucket/*"])
    error_message = "Resource はこのバケットのオブジェクトだけにすること"
  }

  assert {
    condition     = tolist(data.aws_iam_policy_document.bucket.statement[0].condition)[0].variable == "AWS:SourceArn"
    error_message = "SourceArn 条件でこの配信に限定すること"
  }

  assert {
    condition     = tolist(tolist(data.aws_iam_policy_document.bucket.statement[0].condition)[0].values)[0] == "arn:aws:cloudfront::123456789012:distribution/E1EXAMPLE0001"
    error_message = "SourceArn はこの配信の ARN にすること"
  }

  assert {
    condition     = aws_s3_bucket_policy.this.bucket == "example-bucket"
    error_message = "バケットポリシーは配信元バケットに付けること"
  }
}

# 独自ドメインと料金クラスを指定できる
run "custom_aliases_and_price_class" {
  command = plan
  variables {
    aliases     = ["static.example.com", "www.example.com"]
    price_class = "PriceClass_All"
  }

  assert {
    condition     = length(aws_cloudfront_distribution.this.aliases) == 2
    error_message = "aliases をそのまま渡すこと"
  }

  assert {
    condition     = aws_cloudfront_distribution.this.price_class == "PriceClass_All"
    error_message = "price_class を上書きできること"
  }
}

# us-east-1 以外の証明書は弾く
run "rejects_certificate_outside_us_east_1" {
  command = plan
  variables {
    certificate_arn = "arn:aws:acm:ap-northeast-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"
  }
  expect_failures = [var.certificate_arn]
}

# 空の aliases は弾く
run "rejects_empty_aliases" {
  command = plan
  variables {
    aliases = []
  }
  expect_failures = [var.aliases]
}

# 未知の price_class は弾く
run "rejects_unknown_price_class" {
  command = plan
  variables {
    price_class = "PriceClass_50"
  }
  expect_failures = [var.price_class]
}
