module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  version         = "~> 20.0"
  cluster_name    = local.name
  cluster_version = "1.29"

  cluster_endpoint_public_access = true
  enable_irsa                    = true
  subnet_ids                     = module.vpc.private_subnets
  control_plane_subnet_ids       = module.vpc.intra_subnets
  vpc_id                         = module.vpc.vpc_id

  cluster_addons = {
    vpc-cni = {
      version        = "v1.16.2-eksbuild.1"
      before_compute = true
      configuration_values = jsonencode({
        env = {
          ENABLE_PREFIX_DELEGATION = "true"
          WARM_PREFIX_TARGET       = "1"
        }
      })
    }
    kube-proxy = {
      version = "v1.29.0-eksbuild.3"
    }
    coredns = {
      version = "v1.11.1-eksbuild.6"
    }
    aws-ebs-csi-driver = {
      version = "v1.27.0-eksbuild.1"
    }
  }

  access_entries = {
    tokugero = {
      principal_arn = "arn:aws:iam::498931648561:user/tokugero"
      policy_associations = {
        tokugero = {
          policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
          access_scope = {
            type = "cluster"
          }
        }
      }
    },
    terraform = {
      principal_arn = "arn:aws:iam::498931648561:user/terraform-mvusd-awsdemo"
      policy_associations = {
        terraform = {
          policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
          access_scope = {
            type = "cluster"
          }
        }
      }
    }
  }

  eks_managed_node_group_defaults = {
    ami_type       = "AL2_x86_64"
    instance_types = ["t3.medium"]
  }

  eks_managed_node_groups = {
    default_node_group = {
      disk_size     = 50
      ebs_optimized = true

      desired_capacity = 1
      max_capacity     = 2
      min_capacity     = 1
    }
  }

  tags = merge(local.tags, {
    "karpenter.sh/discovery" = local.name
  })
}
