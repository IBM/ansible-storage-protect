# Naming Conventions For Ansible Roles And Playbooks

## File name conventions 
* use lowercase letters and underscores to separate words.
* when statements such as include are used, it is convenient to have file names without hyphens.
* for example: `install_web_ubuntu.yml`

## YAML file extension
* use `yml` instead `yaml`. To be consistent and succinct.

---

## Role naming conventions 
* use lowercase letters and hyphens to separate words
* for example, `web-server` or `database-backup`.

## Task naming convention 
* start with a verb: use an action verb at the beginning of the task name to indicate what the role does.
* start with a capital letter.  for example, `Install Nginx` or `Configure firewall`. 
* no need to end with a period for a few words of task description.

## Variable naming convention
* lowercase letters and underscores to separate words. 
* variable must start with the role name.
* for example, if the role name is `nginx`, the variable name should be `nginx_default_hostname`.

---
