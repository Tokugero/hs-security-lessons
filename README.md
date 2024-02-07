# hs-security-lessons

A framework to deploy, manage, and curate security training modules for high school students.
ansible-vault create --vault-id credentials@prompt ansible/group_vars/all/vault.yml
ansible all --ask-vault-pass -i inventory -m debug -a "msg='User: {{ ansible_user }} / Password: {{ ansible_password }}'"

> create vault password in ~/.ansible/credentials; chmod 0600

## ubuntu vm base prep for kubevirt

1.  install ubuntu desktop
1.  give user/pass ubuntu:ubuntu
1.  install `openssh-server`
1.  run playbook
1.  install `qemu-utils` locally
1.  ensure vhdx is merged properly and not split into snapshot layers
1.  run `qemu-img convert -f vhdx -O qcow2 ubuntu-vm-base.vhdx ubuntu-vm-base.qcow2`
1.  install virtctl

            ```
            export VERSION=v0.41.0
            wget https://github.com/kubevirt/kubevirt/releases/download/${VERSION}/virtctl-${VERSION}-linux-amd64
            ```

1.  Add port forward 18443:8443 to uploadproxy.
1.  upload image `virtctl image-upload dv ubuntu-base --namespace kubevirt-images --size=20Gi --image-path ../images/ubuntu.qcow2 --uploadproxy-url=https://127.0.0.1:18443 --insecure --access-mode ReadWriteOnce --volume-mode filesystem`
