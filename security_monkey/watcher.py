"""
.. module: security_monkey.watcher
    :platform: Unix
    :synopsis: Slurps the current config from AWS and compares it to what has previously
    been recorded in the database to find any changes.

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from botocore.exceptions import ClientError
from deepdiff import DeepHash

from security_monkey.common.PolicyDiff import PolicyDiff
from security_monkey.common.utils import sub_dict
from security_monkey import app, datastore
from security_monkey.datastore import Technology, WatcherConfig, store_exception, Account, IgnoreListEntry, db, \
    ItemRevision, Datastore, durable_hash
from security_monkey.common.jinja import get_jinja_env
from security_monkey.alerters.custom_alerter import report_watcher_changes

from boto.exception import BotoServerError
import time

from copy import deepcopy
import dpath.util
from dpath.exceptions import PathNotFound

import logging

# TODO: Find a better way for the sake of less hair-pulling during unit testing so that this is not a global variable
#       that constantly breaks!!
watcher_registry = {}
abstract_classes = set(['Watcher', 'CloudAuxWatcher', 'CloudAuxBatchedWatcher'])


if not app.config.get("DONT_IGNORE_BOTO_VERBOSE_LOGGERS"):
    logging.getLogger('botocore.vendored.requests.packages.urllib3').setLevel(logging.WARNING)
    logging.getLogger('botocore.credentials').setLevel(logging.WARNING)


class WatcherType(type):
    def __init__(cls, name, bases, attrs):
        super(WatcherType, cls).__init__(name, bases, attrs)
        if cls.__name__ not in abstract_classes and cls.index:
            app.logger.debug("Registering watcher {} {}.{}".format(cls.index, cls.__module__, cls.__name__))
            watcher_registry[cls.index] = cls


class Watcher(object, metaclass=WatcherType):
    """Slurps the current config from AWS and compares it to what has previously
      been recorded in the database to find any changes."""
    index = 'abstract'
    i_am_singular = 'Abstract'
    i_am_plural = 'Abstracts'
    rate_limit_delay = 0
    ignore_list = []
    interval = 60    #in minutes
    active = True
    account_type = 'AWS'

    def __init__(self, accounts=None, debug=False):
        """Initializes the Watcher"""
        self.datastore = datastore.Datastore()
        if not accounts:
            accounts = Account.query.filter(Account.third_party==False).filter(Account.active==True).all()
        else:
            accounts = Account.query.filter(Account.third_party==False).filter(Account.active==True).filter(Account.name.in_(accounts)).all()
        if not accounts:
            raise ValueError('Watcher needs a valid account')
        self.accounts = [account.name for account in accounts]
        self.account_identifiers = [account.identifier for account in accounts]
        self.debug = debug
        self.created_items = []
        self.deleted_items = []
        self.changed_items = []
        self.ephemeral_items = []
        # TODO: grab these from DB, keyed on account
        self.rate_limit_delay = 0
        self.honor_ephemerals = False
        self.ephemeral_paths = []

        # Batching attributes:
        self.batched_size = 0   # Don't batch anything by default
        self.done_slurping = True   # Don't batch anything by default
        self.total_list = []    # This will hold the full list of items to batch over
        self.batch_counter = 0  # Keeps track of the batch we are on -- can be used for retry logic
        self.current_account = None  # Tuple that holds the current account and account index we are on.
        self.technology = None
        # Region is probably not needed if we are using CloudAux's iter_account_region -- will test this in
        # the future as we add more items with batching support.

    def prep_for_slurp(self):
        """
        Should be run before slurp is run to grab the IgnoreList.
        """
        query = IgnoreListEntry.query
        query = query.join((Technology, Technology.id == IgnoreListEntry.tech_id))
        self.ignore_list = query.filter(Technology.name == self.index).all()

    def prep_for_batch_slurp(self):
        """
        Should be run before batching slurps to set the current account (and region).

        This will load the DB objects for account and technology for where we are currently at in the process.
        :return:
        """
        self.prep_for_slurp()

        # Which account are we currently on?
        if not self.current_account:
            index = 0

            # Get the Technology
            # If technology doesn't exist, then create it:
            technology = Technology.query.filter(Technology.name == self.index).first()
            if not technology:
                technology = Technology(name=self.index)
                db.session.add(technology)
                db.session.commit()
                app.logger.info("Technology: {} did not exist... created it...".format(self.index))

            self.technology = technology
        else:
            index = self.current_account[1] + 1

        self.current_account = (Account.query.filter(Account.name == self.accounts[index]).one(), index)

        # We will not be using CloudAux's iter_account_region for multi-account -- we want
        # to have per-account level of batching
        self.total_list = []    # Reset the total list for a new account to run against.
        self.done_slurping = False
        self.batch_counter = 0

    def check_ignore_list(self, name):
        """
        See if the given item has a name flagging it to be ignored by security_monkey.
        """
        for result in self.ignore_list:
            # Empty prefix comes back as None instead of an empty string ...
            prefix = result.prefix or ""
            if name.lower().startswith(prefix.lower()):
                app.logger.info("Ignoring {}/{} because of IGNORELIST prefix {}".format(self.index, name, result.prefix))
                return True

        return False

    def wrap_aws_rate_limited_call(self, awsfunc, *args, **nargs):
        attempts = 0

        def increase_delay():
            if self.rate_limit_delay == 0:
                self.rate_limit_delay = 1
                app.logger.warn(('Being rate-limited by AWS. Increasing delay on tech {} ' +
                                'in account {} from 0 to 1 second. Attempt {}')
                                .format(self.index, self.accounts, attempts))
            elif self.rate_limit_delay < 4:
                self.rate_limit_delay = self.rate_limit_delay * 2
                app.logger.warn(('Still being rate-limited by AWS. Increasing delay on tech {} ' +
                                'in account {} to {} seconds. Attempt {}')
                                .format(self.index, self.accounts, self.rate_limit_delay, attempts))
            else:
                app.logger.warn(('Still being rate-limited by AWS. Keeping delay on tech {} ' +
                                'in account {} at {} seconds. Attempt {}')
                                .format(self.index, self.accounts, self.rate_limit_delay, attempts))

        while True:
            attempts = attempts + 1
            try:
                if self.rate_limit_delay > 0:
                    time.sleep(self.rate_limit_delay)

                retval = awsfunc(*args, **nargs)

                if self.rate_limit_delay > 0:
                    app.logger.warn("Successfully Executed Rate-Limited Function. "
                                    "Tech: {} Account: {}. Removing sleep period."
                                    .format(self.index, self.accounts))
                    self.rate_limit_delay = 0

                return retval
            except BotoServerError as e:  # Boto
                if not e.error_code == 'Throttling':
                    raise e
                increase_delay()
            except ClientError as e:  # Botocore
                if not e.response["Error"]["Code"] == "Throttling":
                    raise e
                increase_delay()

    def created(self):
        """
        Used by the Jinja templates
        :returns: True if created_items is not empty
        :returns: False otherwise.
        """
        return len(self.created_items) > 0

    def deleted(self):
        """
        Used by the Jinja templates
        :returns: True if deleted_items is not empty
        :returns: False otherwise.
        """
        return len(self.deleted_items) > 0

    def changed(self):
        """
        Used by the Jinja templates
        :returns: True if changed_items is not empty
        :returns: False otherwise.
        """
        return len(self.changed_items) > 0

    def slurp_list(self):
        """
        This will fetch all the items in question that will need to get slurped.
        This is used to know what we are going to have to batch up.
        :return:
        """
        raise NotImplementedError()

    def slurp(self):
        """
        method to slurp configuration from AWS for whatever it is that I'm
        interested in. This will be overridden for each technology.
        """
        raise NotImplementedError()

    def slurp_exception(self, location=None, exception=None, exception_map={}, source="watcher"):
        """
        Logs any exceptions that happen in slurp and adds them to the exception_map
        using their location as the key.  The location is a tuple in the form:
        (technology, account, region, item_name) that describes the object where the exception occurred.
        Location can also exclude an item_name if the exception is region wide.
        """
        if location in exception_map:
            app.logger.debug("Exception map already has location {}. This should not happen.".format(location))
        exception_map[location] = exception
        app.logger.debug("Adding {} to the exceptions list. Exception was: {}".format(location, str(exception)))

        # Store it to the database:
        store_exception(source, location, exception)

    def location_in_exception_map(self, item_location, exception_map={}):
        """
        Determines whether a given location is covered by an exception already in the
        exception map.

            Item location: (self.index, self.account, self.region, self.name)
          exception Maps: (index, account, region, name)
                          (index, account, region)
                          (index, account)

            :returns: True if location is covered by an entry in the exception map.
            :returns: False if location is not covered by an entry in the exception map.
        """
        # Exact Match
        if item_location in exception_map:
            app.logger.debug("Skipping {} due to an item-level exception {}.".format(item_location, exception_map[item_location]))
            return True

        # (index, account, region)
        if item_location[0:3] in exception_map:
            app.logger.debug("Skipping {} due to a region-level exception {}.".format(item_location, exception_map[item_location[0:3]]))
            return True

        # (index, account)
        if item_location[0:2] in exception_map:
            app.logger.debug("Skipping {} due to an account-level exception {}.".format(item_location, exception_map[item_location[0:2]]))
            return True

        # (index)
        if item_location[0:1] in exception_map:
            app.logger.debug("Skipping {} due to a technology-level exception {}.".format(item_location, exception_map[item_location[0:1]]))
            return True

        return False

    def find_deleted(self, previous=[], current=[], exception_map={}):
        """
        Find any items that have been deleted since the last run of the watcher.
        Add these items to the deleted_items list.
        """
        prev_map = {item.location(): item for item in previous}
        curr_map = {item.location(): item for item in current}

        item_locations = list(set(prev_map).difference(set(curr_map)))
        item_locations = [item_location for item_location in item_locations if not self.location_in_exception_map(item_location, exception_map)]
        list_deleted_items = [prev_map[item] for item in item_locations]

        for item in list_deleted_items:
            deleted_change_item = ChangeItem.from_items(old_item=item, new_item=None, source_watcher=self)
            app.logger.debug("%s: %s/%s/%s deleted" % (self.i_am_singular, item.account, item.region, item.name))
            self.deleted_items.append(deleted_change_item)

    def find_new(self, previous=[], current=[]):
        """
        Find any new objects that have been created since the last run of the watcher.
        Add these items to the created_items list.
        """
        prev_map = {item.location(): item for item in previous}
        curr_map = {item.location(): item for item in current}

        item_locations = list(set(curr_map).difference(set(prev_map)))
        list_new_items = [curr_map[item] for item in item_locations]

        for item in list_new_items:
            new_change_item = ChangeItem.from_items(old_item=None, new_item=item, source_watcher=self)
            self.created_items.append(new_change_item)
            app.logger.debug("%s: %s/%s/%s created" % (self.i_am_singular, item.account, item.region, item.name))

    def find_modified(self, previous=[], current=[], exception_map={}):
        """
        Find any objects that have been changed since the last run of the watcher.
        Add these items to the changed_items list.
        """
        prev_map = {item.location(): item for item in previous}
        curr_map = {item.location(): item for item in current}

        item_locations = list(set(curr_map).intersection(set(prev_map)))
        item_locations = [item_location for item_location in item_locations if not self.location_in_exception_map(item_location, exception_map)]

        for location in item_locations:
            prev_item = prev_map[location]
            curr_item = curr_map[location]
            # ChangeItem with and without ephemeral changes
            eph_change_item = None
            dur_change_item = None

            if not sub_dict(prev_item.config) == sub_dict(curr_item.config):
                eph_change_item = ChangeItem.from_items(old_item=prev_item, new_item=curr_item, source_watcher=self)

            if self.ephemerals_skipped():
                # deepcopy configs before filtering
                dur_prev_item = deepcopy(prev_item)
                dur_curr_item = deepcopy(curr_item)
                # filter-out ephemeral paths in both old and new config dicts
                if self.ephemeral_paths:
                    for path in self.ephemeral_paths:
                        for cfg in [dur_prev_item.config, dur_curr_item.config]:
                            try:
                                dpath.util.delete(cfg, path, separator='$')
                            except PathNotFound:
                                pass

                # now, compare only non-ephemeral paths
                if not sub_dict(dur_prev_item.config) == sub_dict(dur_curr_item.config):
                    dur_change_item = ChangeItem.from_items(old_item=dur_prev_item, new_item=dur_curr_item,
                                                            source_watcher=self)

                # store all changes, divided in specific categories
                if eph_change_item:
                    self.ephemeral_items.append(eph_change_item)
                    app.logger.debug("%s: ephemeral changes in item %s/%s/%s" % (self.i_am_singular, eph_change_item.account, eph_change_item.region, eph_change_item.name))
                if dur_change_item:
                    self.changed_items.append(dur_change_item)
                    app.logger.debug("%s: durable changes in item %s/%s/%s" % (self.i_am_singular, dur_change_item.account, dur_change_item.region, dur_change_item.name))

            elif eph_change_item is not None:
                # store all changes, handle them all equally
                self.changed_items.append(eph_change_item)
                app.logger.debug("%s: changes in item %s/%s/%s" % (self.i_am_singular, eph_change_item.account, eph_change_item.region, eph_change_item.name))

    def find_changes(self, current=None, exception_map=None):
        """
        Identify changes between the configuration I have and what I had
        last time the watcher ran.
        This ignores any account/region which caused an exception during slurp.
        """
        current = current or []
        exception_map = exception_map or {}

        # Batching only logic here:
        if self.batched_size > 0:
            # Return the items that should be audited:
            return self.find_changes_batch(current, exception_map)

        else:
            prev = self.read_previous_items()
            self.find_deleted(previous=prev, current=current, exception_map=exception_map)
            self.find_new(previous=prev, current=current)
            self.find_modified(previous=prev, current=current, exception_map=exception_map)

    def find_changes_batch(self, items, exception_map):
        # Given the list of items, find new items that don't yet exist:
        durable_items = []

        from security_monkey.datastore_utils import hash_item, detect_change, persist_item
        for item in items:
            complete_hash, durable_hash = hash_item(item.config, self.ephemeral_paths)

            # Detect if a change occurred:
            is_change, change_type, db_item, created_changed = detect_change(
                item, self.current_account[0], self.technology, complete_hash, durable_hash)

            if not is_change:
                continue

            is_durable = (change_type == "durable")

            if is_durable:
                durable_items.append(item)

            if created_changed == 'created':
                self.created_items.append(ChangeItem.from_items(old_item=None, new_item=item, source_watcher=self))

            if created_changed == 'changed':
                db_item.audit_issues = db_item.issues
                db_item.config = db_item.revisions.first().config

                # At this point, a durable change was detected. If the complete hash is the same,
                # then the durable hash is out of date, and this is not a real item change. This could happen if the
                # ephemeral definitions change (this will be fixed in persist_item).
                # Only add the items to the changed item list that are real item changes:
                if db_item.latest_revision_complete_hash != complete_hash:
                    self.changed_items.append(ChangeItem.from_items(old_item=db_item, new_item=item,
                                                                    source_watcher=self))

            persist_item(item, db_item, self.technology, self.current_account[0], complete_hash,
                         durable_hash, is_durable)

        return durable_items

    def find_deleted_batch(self, exception_map):
        from .datastore_utils import inactivate_old_revisions
        existing_arns = [item["Arn"] for item in self.total_list if item.get("Arn")]
        deleted_items = inactivate_old_revisions(self, existing_arns, self.current_account[0], self.technology)

        for item in deleted_items:
            # An inactive revision has already been commited to the DB.
            # So here, we need to pull the last two revisions to build out our
            # ChangeItem.
            recent_revisions=item.revisions.limit(2).all()
            old_config=recent_revisions[1].config
            new_config=recent_revisions[0].config
            change_item = ChangeItem(
                index=item.technology.name, region=item.region,
                account=item.account.name, name=item.name, arn=item.arn,
                old_config=old_config, new_config=new_config, active=False,
                audit_issues=item.issues)
            self.deleted_items.append(change_item)

    def read_previous_items(self):
        """
        Pulls the last-recorded configuration from the database.
        :return: List of all items for the given technology and the given account.
        """
        prev_list = []
        for account in self.accounts:
            prev = self.datastore.get_all_ctype_filtered(tech=self.index, account=account, include_inactive=False)
            # Returns a map of {Item: ItemRevision}
            for item in prev:
                item_revision = prev[item]
                new_item = ChangeItem(index=self.index,
                                      region=item.region,
                                      account=item.account.name,
                                      name=item.name,
                                      new_config=item_revision.config)
                prev_list.append(new_item)

        return prev_list

    def is_changed(self):
        """
        Note: It is intentional that self.ephemeral_items is not included here
        so that emails will not go out about those changes.
        Those changes will still be recorded in the database and visible in the UI.
        :return: boolean whether or not we've found any changes
        """
        return self.deleted_items or self.created_items or self.changed_items

    def issues_found(self):
        """
        Runs through any changed items to see if any have issues.
        :return: boolean whether any changed items have issues
        """
        has_issues = False
        has_new_issue = False
        has_unjustified_issue = False
        for item in self.created_items + self.changed_items:
            if item.audit_issues:
                has_issues = True
                if item.found_new_issue:
                    has_new_issue = True
                    has_unjustified_issue = True
                    break
                for issue in item.confirmed_existing_issues:
                    if not issue.justified:
                        has_unjustified_issue = True
                        break

        return has_issues, has_new_issue, has_unjustified_issue

    def save(self):
        """
        save new configs, if necessary
        """
        app.logger.info("{} deleted {} in {}".format(len(self.deleted_items), self.i_am_plural, self.accounts))
        app.logger.info("{} created {} in {}".format(len(self.created_items), self.i_am_plural, self.accounts))
        for item in self.created_items + self.deleted_items:
            item.save(self.datastore)

        if self.ephemerals_skipped():
            changed_locations = [item.location() for item in self.changed_items]

            new_item_revisions = [item for item in self.ephemeral_items if item.location() in changed_locations]
            app.logger.info("{} changed {} in {}".format(len(new_item_revisions), self.i_am_plural, self.accounts))
            for item in new_item_revisions:
                item.save(self.datastore)

            edit_item_revisions = [item for item in self.ephemeral_items if item.location() not in changed_locations]
            app.logger.info("{} ephemerally changed {} in {}".format(len(edit_item_revisions), self.i_am_plural, self.accounts))
            for item in edit_item_revisions:
                item.save(self.datastore, ephemeral=True)
        else:
            app.logger.info("{} changed {} in {}".format(len(self.changed_items), self.i_am_plural, self.accounts))
            for item in self.changed_items:
                item.save(self.datastore)
        report_watcher_changes(self)

    def plural_name(self):
        """
        Used for Jinja Template
        :return: i_am_plural
        """
        return self.i_am_plural

    def singular_name(self):
        """
        Used for Jinja Template
        :return: i_am_singular
        """
        return self.i_am_singular

    def get_interval(self):
        """ Returns interval time (in minutes) """
        config = WatcherConfig.query.filter(WatcherConfig.index == self.index).first()
        if config:
            return config.interval

        return self.interval

    def is_active(self):
        """ Returns active """
        config = WatcherConfig.query.filter(WatcherConfig.index == self.index).first()
        if config:
            return config.active

        return self.active

    def ephemerals_skipped(self):
        """ Returns whether ephemerals locations are ignored """
        return self.honor_ephemerals


class ChangeItem(object):
    """
    Object tracks two different revisions of a given item.
    """

    def __init__(self, index=None, region=None, account=None, name=None, arn=None, old_config=None, new_config=None,
                 active=False, audit_issues=None, source_watcher=None):
        self.index = index
        self.region = region
        self.account = account
        self.name = name
        self.arn = arn
        self.old_config = old_config if old_config else {}
        self.new_config = new_config if new_config else {}
        self.active = active
        self.audit_issues = audit_issues or []
        self.confirmed_new_issues = []
        self.confirmed_fixed_issues = []
        self.confirmed_existing_issues = []
        self.found_new_issue = False
        self.watcher = source_watcher

    @classmethod
    def from_items(cls, old_item=None, new_item=None, source_watcher=None):
        """
        Create ChangeItem from two separate items.
        :return: An instance of ChangeItem
        """
        if not old_item and not new_item:
            return
        valid_item = new_item if new_item else old_item
        audit_issues = old_item.audit_issues if old_item else []
        active = True if new_item else False
        old_config = old_item.config if old_item else {}
        new_config = new_item.config if new_item else {}
        return cls(index=valid_item.index,
                   region=valid_item.region,
                   account=valid_item.account,
                   name=valid_item.name,
                   arn=valid_item.arn,
                   old_config=old_config,
                   new_config=new_config,
                   active=active,
                   audit_issues=audit_issues,
                   source_watcher=source_watcher)

    @property
    def config(self):
        return self.new_config

    def location(self):
        """
        Construct a location from the object.
        :return: tuple containing index, account, region, and name.
        """
        return (self.index, self.account, self.region, self.name)

    def get_pdiff_html(self):
        pdiff = PolicyDiff(self.new_config, self.old_config)
        return pdiff.produceDiffHTML()

    def _dict_for_template(self):
        return {
            'account': self.account,
            'region': self.region,
            'name': self.name,
            'confirmed_new_issues': self.confirmed_new_issues,
            'confirmed_fixed_issues': self.confirmed_fixed_issues,
            'confirmed_existing_issues': self.confirmed_existing_issues,
            'pdiff_html': self.get_pdiff_html()
        }

    def description(self):
        """
        Provide an HTML description of the object for change emails and the Jinja templates.
        :return: string of HTML describing the object.
        """
        jenv = get_jinja_env()
        template = jenv.get_template('jinja_change_item.html')
        body = template.render(self._dict_for_template())
        # app.logger.info(body)
        return body

    def save(self, datastore, ephemeral=False):
        """
        Save the item
        """
        app.logger.debug("Saving {}/{}/{}/{}\n\t{}".format(self.index, self.account, self.region, self.name, self.new_config))
        self.db_item = datastore.store(
            self.index,
            self.region,
            self.account,
            self.name,
            self.active,
            self.new_config,
            arn=self.arn,
            new_issues=self.audit_issues,
            ephemeral=ephemeral,
            source_watcher=self.watcher)


def ensure_item_has_latest_revision_id(item):
    """
    This is a function that will attempt to correct an item that does not have a latest revision id set.
    There are two outcomes that result:
    1. If there is a revision with the item id, find the latest revision, and update the item such that it
       point to that latest revision.
    2. If not -- then we will treat the item as rancid and delete it from the database.
    :param item:
    :return The item if it was fixed -- or None if it was deleted from the DB:
    """
    if not item.latest_revision_id:
        current_revision = db.session.query(ItemRevision).filter(ItemRevision.item_id == item.id)\
                            .order_by(ItemRevision.date_created.desc()).first()

        if not current_revision:
            db.session.delete(item)
            db.session.commit()

            app.logger.error("[?] Item: {name}/{tech}/{account}/{region} does NOT have a latest revision attached, "
                             "and no current revisions were located. The item has been deleted.".format(
                                name=item.name,
                                tech=item.technology.name,
                                account=item.account.name,
                                region=item.region))

            return None

        else:
            # Update the latest revision ID:
            item.latest_revision_id = current_revision.id

            # Also need to generate the hashes:
            # 1. Get the watcher class of the item:
            watcher_cls = watcher_registry[item.technology.name]
            watcher = watcher_cls(accounts=[item.account.name])
            ds = Datastore()

            # 2. Generate the hashes:
            if watcher.honor_ephemerals:
                ephemeral_paths = watcher.ephemeral_paths
            else:
                ephemeral_paths = []

            item.latest_revision_complete_hash = DeepHash(current_revision.config)[current_revision.config]
            item.latest_revision_durable_hash = durable_hash(current_revision.config, ephemeral_paths)

            db.session.add(item)
            db.session.commit()

            app.logger.error("[?] Item: {name}/{tech}/{account}/{region} does NOT have a latest revision attached, "
                             "but a current revision was located. The item has been fixed.".format(
                                name=item.name,
                                tech=item.technology.name,
                                account=item.account.name,
                                region=item.region))

    return item
