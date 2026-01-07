# ansible-playbook playbook.yml -i inventory.ini \
#   -e sp_source_module_dir=/path/to/repo/IBM/ansible-storage-protect/plugins \
#   --limit sp_server_linux

ansible-playbook playbook.yml -i inventory.ini \
  -e sp_source_module_dir=/path/to/repo/IBM/ansible-storage-protect/plugins \
  --limit sp_server_windows


# ansible-playbook playbook_configure.yml -i inventory.ini \
#   -e sp_source_module_dir=/path/to/repo/IBM/ansible-storage-protect/plugins \
#   --limit sp_server_linux