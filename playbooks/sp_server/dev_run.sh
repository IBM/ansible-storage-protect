# ansible-playbook playbook.yml -i inventory.ini \
#   -e sp_source_module_dir=/mnt/c/Users/NikhilTanni/Downloads/Nikk-dev/IBM/ansible-storage-protect/plugins \
#   --limit sp_server_linux

ansible-playbook playbook.yml -i inventory.ini \
  -e sp_source_module_dir=/mnt/c/Users/NikhilTanni/Downloads/Nikk-dev/IBM/ansible-storage-protect/plugins \
  --limit sp_server_windows


# ansible-playbook playbook_configure.yml -i inventory.ini \
#   -e sp_source_module_dir=/mnt/c/Users/NikhilTanni/Downloads/Nikk-dev/IBM/ansible-storage-protect/plugins \
#   --limit sp_server_linux