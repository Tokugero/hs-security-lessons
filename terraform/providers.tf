provider "aws" {
  region                   = "us-west-2"
  shared_credentials_files = ["./awscreds"]
  profile                  = "default"
}
