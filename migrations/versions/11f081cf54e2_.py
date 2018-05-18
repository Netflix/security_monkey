"""Add unique constraint to the AccountTypeCustomValues table and remove duplicates

Revision ID: 11f081cf54e2
Revises: a9fe9c93ed75
Create Date: 2018-04-06 17:28:33.431400

"""

# revision identifiers, used by Alembic.
revision = '11f081cf54e2'
down_revision = 'a9fe9c93ed75'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base

Session = sessionmaker()
Base = declarative_base()


class AccountType(Base):
    """
    Defines the type of account based on where the data lives, e.g. AWS.
    """
    __tablename__ = "account_type"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(80), unique=True)


class Account(Base):
    """
    Meant to model AWS accounts.
    """
    __tablename__ = "account"
    id = sa.Column(sa.Integer, primary_key=True)
    active = sa.Column(sa.Boolean())
    third_party = sa.Column(sa.Boolean())
    name = sa.Column(sa.String(50), index=True, unique=True)
    notes = sa.Column(sa.String(256))
    identifier = sa.Column(sa.String(256), unique=True)  # Unique id of the account, the number for AWS.
    account_type_id = sa.Column(sa.Integer, sa.ForeignKey("account_type.id"), nullable=False)


class AccountTypeCustomValues(Base):
    """
    Defines the values for custom fields defined in AccountTypeCustomFields.
    """
    __tablename__ = "account_type_values"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(64))
    value = sa.Column(sa.String(256))
    account_id = sa.Column(sa.Integer, sa.ForeignKey("account.id"), nullable=False)


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    results = session.query(AccountTypeCustomValues).all()
    delete_list = []

    seen = {}
    for result in results:
        if seen.get("{}-{}".format(result.account_id, result.name)):
            # We only want to keep the values that are not null -- if they exist:
            if result.value is None:
                print("[+] Marking duplicate account custom field for account with ID: {},"
                      " field name: {}, field Value: NULL for deletion".format(result.account_id, result.name))
                delete_list.append(result)

            else:
                # Replace the seen element with this one:
                print("[+] Replacing OLD duplicate account custom field for account with ID: {},"
                      " field name: {}, old field Value: {}, "
                      "with new field value: {}".format(result.account_id, result.name,
                                                        seen["{}-{}".format(result.account_id, result.name)].value,
                                                        result.value))
                delete_list.append(seen["{}-{}".format(result.account_id, result.name)])
                seen["{}-{}".format(result.account_id, result.name)] = result

        else:
            seen["{}-{}".format(result.account_id, result.name)] = result

    if delete_list:
        print("[-->] Deleting duplicate account custom fields... This may take a while...")
        for d in delete_list:
            session.delete(d)

        session.commit()
        session.flush()
        print("[@] Deleted all duplicate account custom fields.")
    else:
        print("[@] No duplicates found so nothing to delete!")

    print("[-->] Adding proper unique constraint to the `account_type_values` table...")
    op.create_unique_constraint("uq_account_id_name", "account_type_values", ["account_id", "name"])
    print("[@] Completed adding proper unique constraint to the `account_type_values` table.")


def downgrade():
    op.drop_constraint("uq_account_id_name", "account_type_values")
