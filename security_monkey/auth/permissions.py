"""
.. module: security_monkey.auth.permissions
    :platform: Unix
    :copyright: (c) 2018 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.
.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
from flask_principal import Permission, RoleNeed

# Permissions
view_permission = Permission(RoleNeed('View'))
comment_permission = Permission(RoleNeed('Comment'))
justify_permission = Permission(RoleNeed('Justify'))
admin_permission = Permission(RoleNeed('Admin'))

# In the future, additional permissions can be added here.
# See how Netflix/Lemur does it for an example.
