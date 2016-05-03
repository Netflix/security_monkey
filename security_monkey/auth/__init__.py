from .models import RBACRole

anonymous = RBACRole(name="anonymous")

view = RBACRole(name="View")

comment = RBACRole(name="Comment")
comment.add_parent(view)

justify = RBACRole(name="Justify")
justify.add_parent(comment)

admin = RBACRole(name="Admin")
admin.add_parent(justify)
