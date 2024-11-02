#!/bin/bash

echo "------ Ansible deploy -------"
echo "project \:\ "$folder_name
echo "target server\:\ "$target_server

sed -i s/target_server/$target_server/g ./.ansible/hosts
sed -i s/target_server/$target_server/g ./.ansible/docker_remote_launch.yml
sed -i s/my_service/$folder_name/g ./.ansible/docker_remote_launch.yml

ansible-playbook -i .ansible/hosts .ansible/docker_remote_launch.yml