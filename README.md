# hs-security-lessons

A framework to deploy, manage, and curate security training modules for high school students.
ansible-vault create --vault-id credentials@prompt ansible/group_vars/all/vault.yml
ansible all --ask-vault-pass -i inventory -m debug -a "msg='User: {{ ansible_user }} / Password: {{ ansible_password }}'"

> create vault password in ~/.ansible/credentials; chmod 0600
