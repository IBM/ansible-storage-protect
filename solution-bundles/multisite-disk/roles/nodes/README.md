# ibm.storage_protect.nodes

## Description

An Ansible Role to create/update/remove client nodes on IBM Storage Protect.

## Requirements

There are no specific requirements for this role

## Variables

|Variable Name|Default Value|Required|Description|Example|
|:---|:---:|:---:|:---|:---|
|`storage_protect_state`|"present"|no|The state all objects will take unless overridden by object default|'absent'|
|`storage_protect_server_name`|""|yes|URL to the IBM Storage Protect Server.|127.0.0.1|
|`storage_protect_username`|""|no|Admin User on the IBM Storage Protect Server.||
|`storage_protect_password`|""|no|Platform Admin User's password on the Server.||
|`storage_protect_request_timeout`|`10`|no|Specify the timeout in seconds Ansible should use in requests to the IBM Storage Protect host.||
|`storage_protect_nodes`|`see below`|yes|Data structure describing your nodes described below. ||

### Secure Logging Variables

The following Variables compliment each other.
If Both variables are not set, secure logging defaults to false.
The role defaults to False as normally the add nodes task does not include sensitive information.
storage_protect_nodes_secure_logging defaults to the value of storage_protect_secure_logging if it is not explicitly called. This allows for secure logging to be toggled for the entire suite of configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`storage_protect_nodes_secure_logging`|`False`|no|Whether or not to include the sensitive Node role tasks in the log. Set this value to `True` if you will be providing your sensitive values from elsewhere.|
|`storage_protect_secure_logging`|`False`|no|This variable enables secure logging as well, but is shared across multiple roles, see above.|

### Asynchronous Retry Variables

The following Variables set asynchronous retries for the role.
If neither of the retries or delay or retries are set, they will default to their respective defaults.
This allows for all items to be created, then checked that the task finishes successfully.
This also speeds up the overall role.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`storage_protect_async_retries`|30|no|This variable sets the number of retries to attempt for the role globally.|
|`storage_protect_nodes_async_retries`|`{{ storage_protect_async_retries }}`|no|This variable sets the number of retries to attempt for the role.|
|`storage_protect_async_delay`|1|no|This sets the delay between retries for the role globally.|
|`storage_protect_nodes_async_delay`|`storage_protect_async_delay`|no|This sets the delay between retries for the role.|
|`storage_protect_loop_delay`|0|no|This sets the pause between each item in the loop for the roles globally. To help when API is getting overloaded.|
|`storage_protect_nodes_loop_delay`|`storage_protect_loop_delay`|no|This sets the pause between each item in the loop for the role. To help when API is getting overloaded.|
|`storage_protect_async_dir`|`null`|no|Sets the directory to write the results file for async tasks. The default value is set to `null` which uses the Ansible Default of `/root/.ansible_async/`.|

## Data Structure

### Node Variables

For further details on options, see the underlying `ibm.spectrum_protect.node` module. Note that if no default value is set in the code here, the module may have a default value for the option.

|Variable Name|Default Value|Required|type|Description|
|:---:|:---:|:---:|:---:|:---:|
|`name`|""|no|str|name for this node.|
|`schedules`|""|no|list|list of schedules (by name) for this node.|
|`node_password`|""|no|str|Client node password for this node.|
|`node_password_expiry`|""|no|str|Specifies the node_password expiry for this node.|
|`user_id`|""|no|str|Specifies administrative user_id with client owner authority for this node. (Default is NONE)|
|`contact`|""|no|str|Specifies contact information for this node.|
|`policy_domain`|""|no|str|Specifies policy_domain for this node.|
|`compression`|""|no|str|Specifies whether the node compresses files before sending them to the server. Either `client`, `true` or `false`|
|`can_archive_delete`|""|no|bool|Specifies whether the node can delete archived data.|
|`can_backup_delete`|""|no|bool|Specifies whether the node can delete backed-up data.|
|`option_set`|""|no|str|Specifies client option set for this node.|
|`force_password_reset`|""|no|bool|Specifies whether to force a password reset on next login for this node.|
|`node_type`|""|no|str|Specifies node_type for this node. Either `client`, `nas`, `server` or `objectclient`|
|`url`|""|no|str|Specifies url associated with this node.|
|`utility_url`|""|no|str|Specifies utility_url for this node.|
|`max_mount_points`|""|no|int|Specifies max number of mount points for this node.|
|`auto_rename_file_spaces`|""|no|str|Specifies whether file spaces should be automatically renamed for this node. Either `client`, `true` or `false`|
|`keep_mount_points`|""|no|bool|Specifies if mount points should persist after use for this node.|
|`max_transaction_group`|""|no|int|Specifies aximum number of objects in a single transaction group for this node. The default value is 0. Specifying 0 indicates that the node uses the server global value that is set in the server options file.|
|`data_write_path`|""|no|str|Specifies data write path for this node. Either `any`, `lan` or `lanfree`|
|`data_read_path`|""|no|str|Specifies data read path for this node Either `any`, `lan` or `lanfree`.|
|`target_level`|""|no|str|Specifies target replication level for this node.|
|`session_initiation`|""|no|str|Determines whether the session is initiated by the client or server for this node. Either `clientorserver` or `serveronly`|
|`session_ip`|""|no|str|Specifies the client IP address that the server contacts to initiate scheduled events.|
|`session_port`|""|no|int|Specifies the client port number on which the client listens for sessions from the server.|
|`email`|""|no|str|Specifies email address associated with this node.|
|`deduplication`|""|no|str|Specifies deduplication for this node. Either `clientorserver` or `serveronly`.|
|`backup_initiation`|""|no|str|Specifies backup initiation type for this node. Either `all` or `root`.|
|`replication_state`|""|no|str|Specifies the replication state for this node. Either `enabled` or `disabled`.|
|`backup_repl_rule_default`|""|no|str|Specifies default rule for backup replication for this node.|
|`archive_repl_rule_default`|""|no|str|Specifies default rule for archive replication for this node.|
|`space_repl_rule_default`|""|no|str|Specifies default rule for space replication for this node.|
|`recover_damaged`|""|no|bool|Specifies if node should recover damaged objects.|
|`role_override`|""|no|str|Specifies role_override for this node. Either `client`, `server`, `other` or `usereported`.|
|`authentication_method`|""|no|str|Specifies authentication_method for this node. Either `ldap` or `local`.|
|`session_security`|""|no|str|Specifies whether the node must use the most secure settings to communicate for this node. Either `strict` or `transitional`.|
|`split_large_objects`|""|no|bool|Specifies if large objects should be split during backup for this node.|
|`min_extent_size`|""|no|str|Specifies minimum size of extents in KB (50, 250, or 750) for this node.|
|`state`|""|no|str|Desired state for this node.|

### Standard Node Data Structure

```yaml
---
storage_protect_nodes:
  - name: Test_node_1
    node_password: P@ssword123456789
    state: present
    session_security: transitional
    node_password_expiry: 90
    can_archive_delete: true
    min_extent_size: 250
  - name: Test_node_2
    node_password: P@ssword123456789
    state: present
    session_security: transitional
    node_password_expiry: 90
    can_archive_delete: true
    min_extent_size: 250
```

## Playbook Examples

### Standard Role Usage

```yaml
---
- name: Playbook to configure storage_protect nodes
  hosts: localhost
  vars_files:
    - vars/sp_nodes.yml  # Corresponds to the example above
  vars:
    storage_protect_server_name: IBMSPSVR01
    storage_protect_username: adminuser
    storage_protect_password: adminPassword12345678  # For illustration purposes only. You should vault this or retrieve from credential.
  roles:
    - {role: ibm.storage_protect.nodes, when: storage_protect_nodes is defined}
```

## License Information
Apache License, Version 2.0

See [LICENSE](LICENSE) to see the full text.

## Author

[Tom Page](https://github.com/Tompage1994)
