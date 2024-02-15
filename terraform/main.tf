terraform {
  backend "s3" {
    bucket = "terraform-mvusd-demo"
    key    = "mvusd-demo"
    region = "us-west-2"
  }
}

module "eks" {
  source = "./modules/eks"
}

#module "frontend" {
#  source = "./modules/frontend"
#}
