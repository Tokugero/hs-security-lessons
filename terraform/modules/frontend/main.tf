resource "aws_route53_zone" "mvusd-demo-net" {
  name = "mvusd-demo.net"
}

resource "aws_iam_policy" "external-dns" {
  name = "external-dns"

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : [
          "route53:ChangeResourceRecordSets"
        ],
        "Resource" : [
          "arn:aws:route53:::hostedzone/*"
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "route53:List*",
          "route53:Get*"
        ],
        "Resource" : [
          "*"
        ]
      }
    ]
  })
}

data "aws_eks_cluster" "mvusd-demo" {
  name = try("mvusd-demo", null)
}

module "iam_assumable_role_with_oidc" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-assumable-role-with-oidc"
  version = "~> 5.34"

  create_role = true
  role_name   = "external-dns"

  provider_url = data.aws_eks_cluster.mvusd-demo.identity[0].oidc[0].issuer

  role_policy_arns = [
    aws_iam_policy.external-dns.arn,
  ]

  number_of_role_policy_arns = 1
}

resource "aws_iam_role_policy_attachment" "external-dns" {
  role       = module.iam_assumable_role_with_oidc.iam_role_name
  policy_arn = aws_iam_policy.external-dns.arn
}
