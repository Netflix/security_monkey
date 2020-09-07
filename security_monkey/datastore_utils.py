import datetime
from six import text_type

from security_monkey import datastore, app
from cloudaux.orchestration.aws.arn import ARN
from security_monkey.datastore import Item, ItemRevision, hash_item

prims = [int, str, text_type, bool, float, type(None)]


def persist_item(item, db_item, technology, account, complete_hash, durable_hash, durable):
    if not db_item:
        if account.account_type.name != "AWS":
            db_item = create_item(item, technology, account)
        else:
            db_item = create_item_aws(item, technology, account)

    if db_item.latest_revision_complete_hash == complete_hash:
        app.logger.debug("Change persister doesn't see any change. Ignoring...")

        # Check if the durable hash is out of date for some reason. This could happen if the
        # ephemeral definitions change. If this is the case, then update it.
        if db_item.latest_revision_durable_hash != durable_hash:
            app.logger.info("[?] Item: {item} in {account}/{tech} has an out of date durable hash. Updating...".format(
                item=db_item.name, account=account.name, tech=technology.name
            ))
            db_item.latest_revision_durable_hash = durable_hash
            datastore.db.session.add(db_item)
            datastore.db.session.commit()
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
    if list(config.keys()) == ['Arn']:
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
