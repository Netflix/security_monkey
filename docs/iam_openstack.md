IAM Role Setup on OpenStack
===========================

Security Monkey currently only supports the Keystone [password](https://docs.openstack.org/keystoneauth/latest/authentication-plugins.html) identity plugin. 
This allows for support for both V2/V3 identity services. It is anticipated that additional identity plugins will be added.


Credentials
-----------

OpenStack clients have migrated to utilizing the [os-client-config](https://docs.openstack.org/os-client-config/latest/) library for configuation. This supports definition of multiple cloud configs in a single yaml file. The Security Monkey OpenStack integration utilizes os-client-config, where legacy OpenRC files can be formatted into clouds.yaml entries.

    $ cat ~/.config/openstack/clouds.yaml
    clouds:
        openstack:
             auth:
                 auth_url: http://192.168.1.1/identity/v3
                 username: "secmonkey"
                 project_id: 3bb7e8e8e01247ea9401dced0a642093
                 project_name: "demo"
                 password: "XXXXXXXXX"
                 user_domain_name: "Default"
             region_name: "RegionOne"
             interface: "public"
             identity_api_version: 3


Account Setup
-------------

By default, regular users created in a project are considered project owners and have both read and write access to project configurations (i.e., you can view current security groups and also create/delete). If you do not have access to setup or request a read-only role added (below) and plan to use an existing user or create a dedicated security monkey user, understand that user will have orchestration rights.

Example commands below are using the unified openstack client. User creation requires "admin" user rights (can also be performed in Horizon).

    openstack user create secmonkey --password XXXXXXXXX --project demo
    +---------------------+----------------------------------+
    | Field               | Value                            |
    +---------------------+----------------------------------+
    | default_project_id  | 3bb7e8e8e01247ea9401dced0a642093 |
    | domain_id           | default                          |
    | enabled             | True                             |
    | id                  | d206369150994984ad1926821b5ce39b |
    | name                | secmonkey                        |
    | options             | {}                               |
    | password_expires_at | None                             |
    +---------------------+----------------------------------+

Role Setup
----------

OpenStack's support for IAM [roles](https://docs.openstack.org/keystone/latest/admin/cli-manage-projects-users-and-roles.html) continues to evolve. 

Currently, role configuration is an involved/manual process. It requires admin account access to create and assign roles and also the ability to directly edit the OpenStack service policy files (or the ability to set via automated workflow). In addition, roles are managed per service (/etc/PROJECT/policy.json). Modify the user/project names below as appropriate.

We will create a dedicated read-only role and modify service policy to restrict to get APIs. 

    $ openstack role create read-only
    +-----------+----------------------------------+
    | Field     | Value                            |
    +-----------+----------------------------------+
    | domain_id | None                             |
    | id        | 58c2bffb10174664aef7707c0fe6885a |
    | name      | read-only                        |
    +-----------+----------------------------------+

Add the secmonkey user (created above) to the read-only role (this command has no output)

    $ openstack role add --user secmonkey --project demo read-only

Verify the user was added to the role

    $ openstack role assignment list --user secmonkey --project demo --names 
    +-----------+--------------------+-------+--------------+--------+-----------+
    | Role      | User               | Group | Project      | Domain | Inherited |
    +-----------+--------------------+-------+--------------+--------+-----------+
    | read-only | secmonkey@Default  |       | demo@Default |        | False     |
    +-----------+--------------------+-------+--------------+--------+-----------+


These instructions were written based on the Pike release, syntax may look different depending on the release. Let's start where most of our watchers reference, the neutron (networking service) policy file (by default in /etc/neutron/policy.json). There are many ways we could setup the policies to restrict our role to only get APIs. 
One of the least intrusive is to exclude the read_only role from the owner rule and create a read_only rule that we can apply to the get APIs. Then we update each get with an or clause for our read_only rule.

    {
        "context_is_admin":  "role:admin or user_name:neutron",
        "owner": "tenant_id:%(tenant_id)s and not role:read_only",
        "admin_or_owner": "rule:context_is_admin or rule:owner",
        "context_is_advsvc":  "role:advsvc",
        "admin_or_network_owner": "rule:context_is_admin or tenant_id:%(network:tenant_id)s",
        "admin_owner_or_network_owner": "rule:owner or rule:admin_or_network_owner",
        "admin_only": "rule:context_is_admin",
        "read_only": "role:read_only",
        "regular_user": "",
        ...
        "get_network": "rule:admin_or_owner or rule:shared or rule:external or rule:context_is_advsvc or rule:read_only",
        ...
        "get_port": "rule:context_is_advsvc or rule:admin_owner_or_network_owner or rule:read_only",
        ...
        "get_router": "rule:admin_or_owner or rule:read_only",
        ...
        "get_floatingip": "rule:admin_or_owner or rule:read_only",
    }

Changes are effectively immediately, requires no service restart. We have to repeat for each service policy that is supported.

Edit nova (compute service) policy to restrict to only the instance show APIs and security groups (by default, /etc/nova/policy.json).

    {
        "context_is_admin":  "role:admin",
        "admin_or_owner":  "is_admin:True or project_id:%(project_id)s and not role:read_only",
        "read_only": "role:read_only",
        "default": "rule:admin_or_owner",
        "admin_api": "is_admin:True",
        ...
        "os_compute_api:servers:show": "rule:admin_or_owner or rule:read_only",
        "os_compute_api:os-security-groups": "rule:admin_or_owner or rule:read_only",
        ...
    }

Next:
-----

- [Back to the Quickstart](quickstart.md#database)
