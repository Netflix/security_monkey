"""Issue #1003 -- Resolve duplicate entries in the Security Monkey database.

Revision ID: a9fe9c93ed75
Revises: 00c1dabdbe85
Create Date: 2018-03-19 10:05:14.020114

"""

# revision identifiers, used by Alembic.
revision = 'a9fe9c93ed75'
down_revision = '00c1dabdbe85'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base

Session = sessionmaker()
Base = declarative_base()


class IssueItemAssociation(Base):
    __tablename__ = "issue_item_association"
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    super_issue_id = sa.Column(sa.Integer)
    sub_item_id = sa.Column(sa.Integer)


class AssociationTable(Base):
    __tablename__ = "association"
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.Integer)
    account_id = sa.Column(sa.Integer)


class RolesUsers(Base):
    __tablename__ = "roles_users"
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.Integer)
    role_id = sa.Column(sa.Integer)


def remove_duplicate_issue_items():
    bind = op.get_bind()
    session = Session(bind=bind)

    results = session.query(IssueItemAssociation).all()

    seen = {}
    for result in results:
        if seen.get("{}-{}".format(result.sub_item_id, result.super_issue_id)):
            print("[-] Duplicate item association marked for deletion: {} - {}"
                  .format(result.sub_item_id, result.super_issue_id))
            session.delete(result)

        else:
            seen["{}-{}".format(result.sub_item_id, result.super_issue_id)] = True

    print("[-->] Deleting duplicate item associations...")
    session.commit()
    session.flush()
    print("[@] Deleted all duplicate item associations.")


def remove_duplicate_association():
    bind = op.get_bind()
    session = Session(bind=bind)

    results = session.query(AssociationTable).all()

    seen = {}
    for result in results:
        if seen.get("{}-{}".format(result.user_id, result.account_id)):
            print("[-] Duplicate association marked for deletion: {} - {}"
                  .format(result.user_id, result.account_id))
            session.delete(result)

        else:
            seen["{}-{}".format(result.user_id, result.account_id)] = True

    print("[-->] Deleting duplicate associations...")
    session.commit()
    session.flush()
    print("[@] Deleted all duplicate associations.")


def remove_duplicate_role_users():
    bind = op.get_bind()
    session = Session(bind=bind)

    results = session.query(RolesUsers).all()

    seen = {}
    for result in results:
        if seen.get("{}-{}".format(result.user_id, result.role_id)):
            print("[-] Duplicate roles_users marked for deletion: {} - {}"
                  .format(result.user_id, result.role_id))
            session.delete(result)

        else:
            seen["{}-{}".format(result.user_id, result.role_id)] = True

    print("[-->] Deleting duplicate roles_users...")
    session.commit()
    session.flush()
    print("[@] Deleted all duplicate roles_users.")


def upgrade():
    # Step 1: Add an ID field:
    op.add_column("issue_item_association",
                  sa.Column('id', sa.Integer, primary_key=True, autoincrement=True))
    op.add_column("association",
                  sa.Column('id', sa.Integer, primary_key=True, autoincrement=True))
    op.add_column("roles_users",
                  sa.Column('id', sa.Integer, primary_key=True, autoincrement=True))

    remove_duplicate_issue_items()
    remove_duplicate_association()
    remove_duplicate_role_users()

    # Alter the table so that there are unique constraints:
    print("[ ] Setting primary key values for the 'issue_item_association' table...")
    op.drop_column("issue_item_association", "id")
    op.create_primary_key("pk_issue_item_association", "issue_item_association", ["super_issue_id", "sub_item_id"])
    print("[+] Completed setting primary key values for 'issue_item_association'")

    print("[ ] Setting primary key values for the 'association' table...")
    op.drop_column("association", "id")
    op.create_primary_key("pk_association", "association", ["user_id", "account_id"])
    print("[+] Completed setting primary key values for 'association'")

    print("[ ] Setting primary key values for the 'roles_users' table...")
    op.drop_column("roles_users", "id")
    op.create_primary_key("pk_roles_users", "roles_users", ["user_id", "role_id"])
    print("[+] Completed setting primary key values for 'roles_users'")

    print("[+] Done!")


def downgrade():
    op.drop_constraint("pk_issue_item_association", "issue_item_association", type_="primary")
    op.drop_constraint("pk_association", "association", type_="primary")
    op.drop_constraint("pk_roles_users", "roles_users", type_="primary")
