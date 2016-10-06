**********************
Development Guidelines
**********************

Adding a Watcher
----------------
Watchers are located in the `watchers <../security_monkey/watchers/>`_ directory. Some related
watcher types are grouped together in common sub directories. An example would be IAM types.

If a watcher is specific to an organization and is not intended to be contributed
back to the OSS community, it should be placed under the watchers/custom directory.

Any class that extends Watcher, overrides index and is located under the watchers
directory will be dynamically loaded by the Security Monkey application at runtime.

All watchers extend the Watcher class located in the `watcher.py <../security_monkey/watcher.py>`_ file. This
base class implements common functionality such as storing items to the database and
determining which items are new, changed or deleted. Some related watchers also have
a common base class to implement common functionality. Examples would be IAM watchers.

Each watcher implementation must override the following:

1. The slurp() method pulls the current set of items in scheduled intervals.
2. The watcher should implement a subclass of the ChangeItem found in the watcher module that is specific to the type the watcher will be pulling in the slurp method
3. The member variables index must be overridden with a unique String that will identify the item type in the database.
4. the member variables i_am_singular and i_am_plural must be overridden with unique values for use in logging.

Watchers may benefit from using the `joblib` library to parallelize the processing of jobs. This will substantially increase
performance of the watcher, especially for those requiring multiple API calls to fetch relevant data. Refer to
`IAMRole Watcher <../security_monkey/watchers/iam/iam_role.py>`_ for an example.

Sample Watcher structure::

    from security_monkey.watcher import Watcher
    from security_monkey.watcher import ChangeItem

    class Sample(Watcher):
        index = 'sample'
        i_am_singular = 'Sample'
        i_am_plural = 'Samples'

    def __init__(self, accounts=None, debug=False):
        super(Sample, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        # Look up relevant items, convert to list of SampleItem's, return list

    class SampleItem(ChangeItem):
        def __init__(self, account=None, name=None, region=None, config={}):
            super(SampleItem, self).__init__(
                    index=Sample.index,
                    region=region,
                    account=account,
                    name=name,
                    new_config=config)

New Watchers may also require additional code:

- If the api to access the system to be watched requires an explicit connection, connection functionality should be placed in the `sts_connect <../security_monkey/common/sts_connect.py>`_ module.

Adding an Auditor
------------------
A watcher may have one or more associated Auditors that will be run against all new or modified
items to determine if there are any security issues. In order to be associated with a Watcher,
the auditor class must override the index to match that of it's associated watcher.

If an auditor is specific to an organization and is not intended to be contributed
back to the OSS community, it should be placed under the auditors/custom directory.

Any class extending Auditor, overriding index and residing under the `auditors <../security_monkey/auditors/>`_ directory.
will be dynamically loaded and considered for execution agains a watcher. As with the related
watchers, closely related auditors may be grouped within sub directories or have base classes
with common functionality.


All auditors override the `Auditor <../security_monkey/auditor.py>`_ base class. Minimal
functionality would override the index, i_am_singular and i_am_plural to match those
in the associated watcher class. In addition, at least one method starting with 'check_'
would be present, as each method starting with 'check_' will be run against new or
changed items returned by the watcher::

    from security_monkey.watchers.sample import Sample

    class SampleAuditor(Auditor):
        index = Sample.index
        i_am_singular = Sample.i_am_singular
        i_am_plural = Sample.i_am_plural

        def __init__(self, accounts=None, debug=False):
            super(SampleAuditor, self).__init__(accounts=accounts, debug=debug)

        check_xxx(self, sample_item):
            # check the item for security risks
            if risk:
                self.add_issue(0, 'issue message', sample_item, notes='optional notes')

If an issue is found, the 'check_' method should call add_issue to save the issue to
the database.
