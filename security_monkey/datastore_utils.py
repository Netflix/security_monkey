import hashlib
import json

import datetime
import dpath.util
from dpath.exceptions import PathNotFound
from copy import deepcopy

from security_monkey import datastore, app
from cloudaux.orchestration.aws.arn import ARN
from security_monkey.datastore import Item, ItemRevision, ItemAudit

prims = [int, str, unicode, bool, float, type(None)]


def persist_item(item, db_item, technology, account, complete_hash, durable_hash, durable):
    if not db_item:
        if account.account_type.name != "AWS":
            db_item = create_item(item, technology, account)
        else:
            db_item = create_item_aws(item, technology, account)

    if db_item.latest_revision_complete_hash == complete_hash:
        app.logger.debug("Change persister doesn't see any change. Ignoring...")
        return

    # Create the new revision
    if durable:
        revision = create_revision(item.config, db_item)
        db_item.revisions.append(revision)

    # Ephemeral -- update the existing revision:
    else:
        revision = db_item.revisions.first()
        revision.date_last_ephemeral_change = datetime.datetime.utcnow()
        revision.config = item.config
        app.logger.debug("Persisting EPHEMERAL change to item: {technology}/{account}/{item}".format(
            technology=technology.name, account=account.name, item=db_item.name
        ))

    db_item.latest_revision_complete_hash = complete_hash
    db_item.latest_revision_durable_hash = durable_hash

    datastore.db.session.add(db_item)
    datastore.db.session.add(revision)
    datastore.db.session.commit()

    if durable:
        app.logger.debug("Persisting DURABLE change to item: {technology}/{account}/{item}".format(
            technology=technology.name, account=account.name, item=db_item.name
        ))
        datastore.db.session.refresh(revision)
        db_item.latest_revision_id = revision.id
        datastore.db.session.add(revision)
        datastore.db.session.add(db_item)
        datastore.db.session.commit()


def is_active(config):
    if config.keys() == ['Arn']:
        return False

    if set(config.keys()) == {'account_number', 'technology', 'region', 'name'}:
        return False

    return True


def create_revision(config, db_item):
    return ItemRevision(
        active=is_active(config),
        config=config,
        item_id=db_item.id,
    )


def create_item_aws(item, technology, account):
    arn = ARN(item.config.get('Arn'))
    return Item(
        region=arn.region or 'universal',
        name=arn.parsed_name or arn.name,
        arn=item.config.get('Arn'),
        tech_id=technology.id,
        account_id=account.id
    )


def create_item(item, technology, account):
    return Item(
        region=item.region or 'universal',
        name=item.name,
        arn=item.arn,
        tech_id=technology.id,
        account_id=account.id
    )



def detect_change(item, account, technology, complete_hash, durable_hash):
    """
    Checks the database to see if the latest revision of the specified
    item matches what Security Monkey has pulled from AWS.

    Note: this method makes no distinction between a changed item, a new item,
    a deleted item, or one that only has changes in the ephemeral section.

    :param item: dict describing an item tracked by Security Monkey
    :param hash: hash of the item dict for quicker change detection
    :return: bool. True if the database differs from our copy of item
    """
    result = result_from_item(item, account, technology)

    # new item doesn't yet exist in DB
    if not result:
        app.logger.debug("Couldn't find item: {tech}/{account}/{region}/{item} in DB.".format(
            tech=item.index, account=item.account, region=item.region, item=item.name
        ))
        return True, 'durable', result, 'created'

    if result.latest_revision_durable_hash != durable_hash:
        app.logger.debug("Item: {tech}/{account}/{region}/{item} in DB has a DURABLE CHANGE.".format(
            tech=item.index, account=item.account, region=item.region, item=item.name
        ))
        return True, 'durable', result, 'changed'

    elif result.latest_revision_complete_hash != complete_hash:
        app.logger.debug("Item: {tech}/{account}/{region}/{item} in DB has an EPHEMERAL CHANGE.".format(
            tech=item.index, account=item.account, region=item.region, item=item.name
        ))
        return True, 'ephemeral', result, None

    else:
        app.logger.debug("Item: {tech}/{account}/{region}/{item} in DB has NO CHANGE.".format(
            tech=item.index, account=item.account, region=item.region, item=item.name
        ))
        return False, None, result, None


def result_from_item(item, account, technology):
    # Construct the query to obtain the specific item from the database:
    return datastore.Item.query.filter(Item.name == item.name, Item.region == item.region,
                                       Item.account_id == account.id, Item.tech_id == technology.id).scalar()


def inactivate_old_revisions(watcher, arns, account, technology):
    result = Item.query.filter(
        Item.account_id == account.id,
        Item.tech_id == technology.id,
        Item.arn.notin_(arns)
    ).join((ItemRevision, Item.latest_revision_id == ItemRevision.id)) \
        .filter(ItemRevision.active == True).all()  # noqa

    for db_item in result:
        app.logger.debug("Deleting {technology}/{account}/{name}".format(
            technology=technology.name, account=account.name, name=db_item.name
        ))

        # Create the new revision
        config = {"Arn": db_item.arn}
        revision = create_revision(config, db_item)
        db_item.revisions.append(revision)

        complete_hash, durable_hash = hash_item(config, watcher.ephemeral_paths)

        db_item.latest_revision_complete_hash = complete_hash
        db_item.latest_revision_durable_hash = durable_hash

        # Add the revision:
        datastore.db.session.add(db_item)
        datastore.db.session.add(revision)
        datastore.db.session.commit()

        # Do it again to update the latest revision ID:
        datastore.db.session.refresh(revision)
        db_item.latest_revision_id = revision.id
        datastore.db.session.add(db_item)

        datastore.db.session.commit()

    return result


def hash_item(config, ephemeral_paths):
    """
    Finds the hash of a dict.

    :param ephemeral_paths:
    :param config:
    :param item: dictionary, typically representing an item tracked in SM
                 such as an IAM role
    :return: hash of the json dump of the item
    """
    complete = hash_config(config)
    durable = durable_hash(config, ephemeral_paths)
    return complete, durable


def durable_hash(config, ephemeral_paths):
    durable_item = deepcopy(config)
    for path in ephemeral_paths:
        try:
            dpath.util.delete(durable_item, path, separator='$')
        except PathNotFound:
            pass
    return hash_config(durable_item)


def hash_config(config):
    item = sub_dict(config)
    item_str = json.dumps(item, sort_keys=True)
    item_hash = hashlib.md5(item_str) # nosec: not used for security
    return item_hash.hexdigest()


def sub_list(l):
    """
    Recursively walk a data-structure sorting any lists along the way.

    :param l: list
    :return: sorted list, where any child lists are also sorted.
    """
    r = []

    for i in l:
        if type(i) in prims:
            r.append(i)
        elif type(i) is list:
            r.append(sub_list(i))
        elif type(i) is dict:
            r.append(sub_dict(i))
        else:
            print "Unknown Type: {}".format(type(i))
    r = sorted(r)
    return r


def sub_dict(d):
    """
    Recursively walk a data-structure sorting any lists along the way.

    :param d: dict
    :return: dict where any lists, even those buried deep in the structure, have been sorted.
    """
    r = {}
    for k in d:
        if type(d[k]) in prims:
            r[k] = d[k]
        elif type(d[k]) is list:
            r[k] = sub_list(d[k])
        elif type(d[k]) is dict:
            r[k] = sub_dict(d[k])
        else:
            print "Unknown Type: {}".format(type(d[k]))
    return r
