class RBACRole(object):
    """
    This model provides core permission functionality.
    """

    roles = {}

    def __init__(self, name=None):
        self.name = name
        if not hasattr(self.__class__, 'parents'):
            self.parents = set()
        if not hasattr(self.__class__, 'children'):
            self.children = set()
        RBACRole.roles[name] = self

    def add_parent(self, parent):
        """
        Add a parent to this role,
        and add role itself to the parent's children set.
        you should override this function if neccessary.
        """
        parent.children.add(self)
        self.parents.add(parent)

    def add_parents(self, *parents):
        """Add parents to this role. Also should override if neccessary.
        Example::

            editor_of_articles = RoleMixin('editor_of_articles')
            editor_of_photonews = RoleMixin('editor_of_photonews')
            editor_of_all = RoleMixin('editor_of_all')
            editor_of_all.add_parents(editor_of_articles, editor_of_photonews)

        :param parents: Parents to add.
        """
        for parent in parents:
            self.add_parent(parent)

    def get_parents(self):
        for parent in self.parents:
            yield parent
            for grandparent in parent.get_parents():
                yield grandparent

    def get_children(self):
        for child in self.children:
            yield child
            for grandchild in child.get_children():
                yield grandchild

    @staticmethod
    def get_by_name(name):
        """A static method to return the role which has the input name.

        :param name: The name of role.
        """
        return RBACRole.roles[name]


class RBACUserMixin(object):
    """
    Provides basic role functionality to users.
    """

    def get_roles(self):
        roles = [RBACRole.roles["anonymous"]]
        if self.role:
            role = RBACRole.roles[self.role]
            if role:
                roles.append(role)

        return roles
