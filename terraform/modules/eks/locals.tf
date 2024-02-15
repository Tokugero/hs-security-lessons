locals {
  name            = "mvusd-demo"
  cluster_version = "1.29"
  region          = "us-west-2"

  vpc_cidr = "10.1.0.0/16"
  azs      = slice(data.aws_availability_zones.available.names, 0, 3)

  tags = {
    mvusd-demo = "true"
  }
}
