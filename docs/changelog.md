Changelog
=========

v1.0.0 (2018-02-19)
--------------------
Major Milestone release.

There are many, many changes that have been made.  Below are some of the most important items to keep note of:

1. **BREAKING CHANGES -- ALL NEW DEPLOYMENT MODEL** (Please review the [Quickstart](quickstart.md) and [Autostarting](autostarting.md) docs for details)
    - We swapped out APScheduler in favor of Celery. This allows us to actually scale Security Monkey with multiple UI instances, and many, many workers so
      you can get data into Security Monkey much faster!
1. Lots, and lots of bug fixes and documentation updates
1. New features:
    - OpenStack watching and auditing support
    - GitHub Organization, Repos, and Teams watching and auditing
    - AWS GovCloud Support
    - Azure AD SSO provider support
    - AWS Glacier support
    - Support for [SWAG account syncing](https://github.com/Netflix-Skunkworks/swag-client).
    - Auditor improvements
    - Ability to import bulk network whitelists (and via S3)

1. Many IAM changes. [Please review the IAM docs](https://github.com/Netflix/security_monkey/blob/develop/docs/quickstart.md#account-types) and update your permissions accordingly.

Too many PRs to list... Special thanks to the following contributors:
    - @mikegrima
    - @monkeysecurity
    - @mstair
    - @kevgliss
    - @mcpeak
    - @zpritcha
    - @mark-ignacio
    - @falcoris
    - @vishbhalla
    - @frohoff
    - @tabletcorry
    - @shrikant0013
    - @pjbgf
    - @billy-lechtenberg
    - @Qmando
    - @jleaniz
    - @wozz
    - @markofu
    - @cxmcc
    - @jpohjolainen
    - @PyScott
    - @sysboy
    - @gellerb
    - @fabiop
    - @joaquin386
    - @oba11
    - @castrapel
    - @NunoPinheiro
    - @apettinen
    - @johnclaus

**KNOWN BUGS** Daily emails are not getting sent out. See #953

v0.9.3 (2017-07-31)
----------------------------------------

Important Notes:
- Additional Permissions Requried:
    - "lambda:getfunctionconfiguration",
    - "lambda:getpolicy",
    - "lambda:listaliases",
    - "lambda:listeventsourcemappings",
    - "lambda:listtags",
    - "lambda:listversionsbyfunction",
    - "lambda:listfunctions",


v0.9.2 (2017-05-24)
----------------------------------------

- PR #695 - @mikegrima - Fixing jinja import bug affecting change emails.
- PR #692 - @LukeKennedy - Reduce number of API calls in Managed Policy watcher.
- PR #694 - @supertom - GCP Documentation Updates
- PR #701 - @supertom - Update GCP ServiceAccount Name to use email instead of DisplayName.
- PR #702 - @rodriguezsergio - Update KMS Auditor. Don't create issue when Effect is Deny for a wildcard principal.
- PR #697 - @mcpeak - Pylint fixes and TravisCI pylint enforcement.
- PR #706 - @monkeysecurity Fix bug where batched watchers did not send change alert emails.
- PR #708 - @redixin - Fix bug in docker config where `SECURITY_MONKEY_POSTGRES_PORT` would not work if passed as a string.
- PR #714 - @monkeysecurity - Fix bug where change emails from batched watchers had incorrect color in the JSON diff.
- PR #713 - @monkeysecurity - Fix path to favicon from flask-security jinja templates.
- PR #709 - @crruthe - Exempt SSO API from CSRF protection.
- PR #719 - @monkeysecurity - New simplified watcher format for CloudAux Technologies.
- PR #726 - @monkeysecurity, @willbengtson - Add new SAMLProvider watcher.
- PR #730 - @monkeysecurity - Fix bug where ephemerals were not respected for CloudAuxWatcher subclasses.
- PR #727 - @supertom - Fix bug where duplicate GCP names would violate DB's unique constraint. Names now contain project ID.
- PR #728 - @supertom - Basic Auditor Tests for GCP.
- @monkeysecurity - Updated link to Ubuntu's SSL documentation.
- @monkeysecurity - Bumped version of Cryptography dependency.
- PEP8 updates.

Important Notes:
- Additional Permissions Required:
    - "elasticloadbalancing:describelisteners",
    - "elasticloadbalancing:describerules",
    - "elasticloadbalancing:describesslpolicies",
    - "elasticloadbalancing:describetags",
    - "elasticloadbalancing:describetargetgroups",
    - "elasticloadbalancing:describetargetgroupattributes",
    - "elasticloadbalancing:describetargethealth",
    - "iam:listsamlproviders",
- New Watcher: ALB (elbv2)
- ELB (v1) Watcher re-written with boto3 in CloudAux.  Now respects the config value `SECURITYGROUP_INSTANCE_DETAIL` when determining whether to add the instance id's to the ELB definition.
 
Contributors:
- @LukeKennedy
- @rodriguezsergio
- @redixin
- @crruthe
- @supertom
- @mcpeak
- @mikegrima
- @monkeysecurity

v0.9.1 (2017-04-20)
----------------------------------------

- PR #666 - @redixin - Use find_packages in setup.py to include nested packages.
- PR #667 - @monkeysecurity - Explicitly adding `urllib3[secure]` to setup.py (REVERTED in #683)
- PR #668 - @monkeysecurity - IPv6 support in security groups.
- PR #669 - @monkeysecurity - Updating the security group auditor to treat `::/0` the same as `0.0.0.0/0`
- PR #671 - @monkeysecurity - Enhancing PolicyDiff to be able to handle non-ascii strings.
- PR #673 - @monkeysecurity - Fixing path to `aws_accounts.json`. (Broken my moving `manage.py`)
- PR #675 - @monkeysecurity - Adding `package_data` and `data_files` sections to setup.py.
- PR #677 - @willbengtson - Fixing the security trackable information.
- PR #682 - @monkeysecurity - Updating packaged supervisor config to provide full path to `monkey`
- PR #681 - @AlexCline - Add reference_policies for TLS transitional ELB security policies
- PR #684 - @monkeysecurity - Disabling DB migration `b8ccf5b8089b`. Was freezing some `db upgrades`
- PR #683 - @monkeysecurity - Reverted #667.  Added `pip install --upgrade urllib3[secure]` to `quickstart` and `Dockerfile`.
- PR #685 - @monkeysecurity - Running `docker-compose build` in Travis-CI.
- PR #688 - @mcpeak - Add Bandit gate to Security Monkey.
- PR #687 - @mikegrima - Fix for issue #680. (Unable to edit account names)
- PR #689 - @mikegrima - Enhancements to Travis-CI: parallelized the workloads. (docker/python/dart in parallel)

Important Notes:
 - This is a hotfix release to correct a number of installation difficulties reported since `0.9.0`.

Contributors:
- @redixin
- @AlexCline
- @willbengtson
- @mcpeak
- @mikegrima
- @monkeysecurity

v0.9.0 (2017-04-13)
----------------------------------------

- PR #500 - @monkeysecurity - Updating ARN.py to look for StringEqualsIgnoreCase in policy condition blocks
- PR #511 - @kalpatel01 - Fix KMSAuditor exceptions
- PR #510 - @kalpatel01 - Add additional JIRA configurations
- PR #504 - @redixin - Plugins support
- PR #515 - @badraufran - Add ability to press enter to search in search bar component
- PR #514 - @badraufran - Update dev_setup_osx.rst to get it up-to-date
- PR #513 / #545- @mikegrima - Fix for S3 watcher errors.
- PR #516  - @badraufran - Remove broken packages link
- PR #518 - @badraufran  - Update `dev_setup_osx` (Remove sudo)
- PR #519 - @selmanj - Minor reformatting/style changes to Docker docs
- PR #512 / #521 - @kalpatel01 - Organize tests into directories
- PR #524 - @kalpatel01 - Remove DB mock class
- PR #522 - @kalpatel01 - Optimize SQL for account delete 
- PR #525 - @kalpatel01 - Handle known kms boto exceptions
- PR #529 - @mariusgrigaitis - Usage of `GOOGLE_HOSTED_DOMAIN` in sample configs
- PR #532 - @kalpatel01 - Add sorting to account tables (UI)
- PR #538 - @cu12 - Add more Docker envvars
- PR #536 / #540 - @supertom - Add account type field to item, item details and search bar.
- PR #534 / #541 - @kalpatel01 - Add bulk enable and disable account service
- PR #546 - @supertom - GCP: fixed accounttypes typo.
- PR #547 - @monkeysecurity - Delete deprecated Account fields
- PR #528 - @kalpatel01 - Fix reaudit issue for watchers in different intervals
- PR #553 - @mikegrima - Fixed bugs in the ES watcher
- PR #535 / #552 - @kalpatel01 - Add support for overriding audit scores
- PR #560 / #587 - @mikegrima - Bump CloudAux version
- PR #533 / #559 - @kalpatel01 - Add Watcher configuration
- PR #562 - @monkeysecurity - Re-adding reporter timing information to the logs.
- PR #557 - @kalpatel01 - Add justified issues report
- PR #573 - @monkeysecurity - fixing issue duplicate ARN issue…
- PR #564 - @kalpatel01 - Fix justification preservation bug
- PR #565 - @kalpatel01 - Handle unicode name tags
- PR #571 - @kalpatel01 - Explicitly set export filename
- PR #572 - @kalpatel01 - Fix minor watcher bugs
- PR #576 - @kalpatel01 - Set user role via SSO profile
- PR #569 - @kalpatel01 - Split `check_access_keys` method in the IAM User Auditor
- PR #566 - @kalpatel01 - Convert watchers to boto3
- PR #568 - @kalpatel01 - Replace ELBAuditor DB query with support watcher
- PR #567 - @kalpatel01 - Reduce AWS managed policy audit noise
- PR #570 - @kalpatel01 - Add support for custom watcher and auditor alerters
- PR #575 - @kalpatel01 - Add functionality to clean up stale issues
- PR #582 - @supertom - [GCP] Watchers/Auditors for GCP
- PR #588 - @supertom - GCP docs: Draft of GCP changes
- PR #592 - @monkeysecurity - SSO Role Modifications
- PR #597 - @supertom - GCP: fixed issue where client wasn't receiving user-specified creds
- PR #598 - @redixin - Implement `add_account_%s` for custom accounts
- PR #600 - @supertom - GCP: fixed issue where bucket watcher wasn't sending credentials to Cloudaux
- PR #602 - @crruthe - Added permission for DescribeVpnGateways missing
- PR #605 - @monkeysecurity - ELB Auditor - Fixing reference to check_rfc_1918
- PR #610 - @monkeysecurity - Adding Unique Index to TechName and AccountName
- PR #612 - @carise - Add a section on using GCP Cloud SQL Postgres with Cloud SQL Proxy
- PR #613 - @monkeysecurity - Setting Item.issue_count to deferred. Only joining tables in distinct if necessary.
- PR #614 - @monkeysecurity - Increasing default timeout
- PR #607 - @supertom - GCP: Set User Agent
- PR #609 - @mikegrima - Added ephemeral section to S3 for "GrantReferences"
- PR #611 - @roman-vynar - Quick start improvements
- PR #619 - @mikegrima - Fix for plaintext passwords in DB if using CLI for user creation
- PR #622 - @jonhadfield - Fix ACM certificate ImportedAt timestamp
- PR #616 - @redixin - Fix docs and variable names related to custom alerters
- PR #502 - @mikegrima - Batching support for watchers
- PR #631 - @supertom - Added `__version__` property
- PR #632 - @sysboy - Set the default value of SECURITY_REGISTERABLE to False
- PR #629 - @BobPeterson1881 - Fix security group rule parsing
- PR #630 - @BobPeterson1881 - Update dashboard view filter links
- PR #633 - @sysboy - Log Warning when S3 ACL can't be retrieved.
- PR #639 - @monkeysecurity - Removing reference to zerotodocker.
- PR #624 - @mikegrima - Adding utilities to get S3 canonical IDs.
- PR #640 - @supertom - GCP: fixed UI Account Type filtering
- PR #642 - @monkeysecurity - Adding active and third_party flags to account view API
- PR #646 - @monkeysecurity - Removing s3_name from exporter and renaming Account.number to identifier
- PR #648 - @mikegrima - Fix for UI Account creation bug
- PR #657 #658 - @jeyglk - Fix Docker
- PR #655 - @monkeysecurity - Updating quickstart/install documentation to simplify.
- PR #659 - @monkeysecurity - Quickstart GCP Fixes
- PR #625 - @bungoume - Fix principal KeyError
- PR #662 - @monkeysecurity - Replacing `python manage.py` with `monkey`
- PR #660 - @mcpeak - Adding an option to allow group write for logfiles
- PR #661 - @shrikant0013 - Added doc on update/upgrade steps

Important Notes:

- `SECURITY_MONKEY_SETTINGS` is no longer a required environment variable.
    - If supplied, security_monkey will respect the variable.  Otherwise it will default to env-config/config.py
- `manage.py` has been moved inside the package and a `monkey` alias has been setup.
    - Where you might once call `python manage.py <arguments>` you will now call `monkey <arguments>`
- Documentation has been converted from RST to Markdown.
    - I will no longer be using readthedocs or RST.
    - Quickstart guide has been largely re-written.
    - Quickstart now instructs you to create and use a virtualenv (and how to get supervisor to work with it)
- This release contains [GCP Watcher Support](https://medium.com/@Netflix_Techblog/netflix-security-monkey-on-google-cloud-platform-gcp-f221604c0cc7).
- Additional Permissions Required:
    - ec2:DescribeVpnGateways

Contributors:
- @kalpatel01
- @redixin
- @badraufran
- @selmanj
- @mariusgrigaitis
- @cu12
- @supertom
- @crruthe
- @carise
- @roman-vynar
- @jonhadfield
- @sysboy
- @jeyglk
- @bungoume
- @mcpeak
- @shrikant0013
- @mikegrima
- @monkeysecurity
 

v0.8.0 (2016-12-02-delayed-\>2017-01-13)
----------------------------------------

-   PR \#425 - @crruthe - Fixed a few report hyperlinks.
-   PR \#428 - @nagwww - Documentation fix. Renamed module: security\_monkey.auditors.elb to module: security\_monkey.auditors.elasticsearch\_service
-   PR \#424 - @mikegrima - OS X Install doc updates for El Capitan and higher.
-   PR \#426 - @mikegrima - Added "route53domains:getdomaindetail" to permissions doc.
-   PR \#427 - @mikegrima - Fix for ARN parsing of cloudfront ARNs.
-   PR \#431 - @mikegrima - Removed s3 ARN check for ElasticSearch Service.
-   PR \#448 - @zollman - Fix exception logging in store\_exception.
-   PR \#444 - @zollman - Adds exception logging listener for appscheduler.
-   PR \#454 - @mikegrima - Updated S3 Permissions to reflect latest changes to cloudaux.
-   PR \#455 - @zollman - Add Dashboard.
-   PR \#456 - @zollman - Increase issue note size.
-   PR \#420 - @crruthe - Added support for SSO OneLogin.
-   PR \#432 - @robertoriv - Add pagination for whitelist and ignore list.
-   PR \#438 - @AngeloCiffa - Pin moto==0.4.25. (TODO: Bump Jinja2 version.)
-   PR \#433 - @jnbnyc - Added Docker/Docker Compose support for local dev.
-   PR \#408 - @zollman - Add support for custom account metadata. (An important step that will allow us to support multiple cloud providers in the future.)
-   PR \#439 - @monkeysecurity - Replace botor lib with Netflix CloudAux.
-   PR \#441 - @monkeysecurity - Auditor ChangeItems now receive ARN.
-   PR \#446 - @zollman - Fix item 'first\_seen' query .
-   PR \#447 - @zollman - Refactor rdsdbcluster array params.
-   PR \#445 - @zollman - Make misfire grace time and reporter start time configurable.
-   PR \#451 - @monkeysecurity - Add coverage with Coveralls.io.
-   PR \#452 - @monkeysecurity - Refactor & add tests for the PolicyDiff module.
-   PR \#449 - @monkeysecurity - Refactoring s3 watcher to use Netflix CloudAux.
-   PR \#453 - @monkeysecurity - Fixing two policy diff cases.
-   PR \#442 - @monkeysecurity - Adding index to region. Dropping unused item.cloud.
-   PR \#450 - @monkeysecurity - Moved test & onelogin requirements to the setup.py extras\_require section.
-   PR \#407 - @zollman - Link together issues by enabling auditor dependencies.
-   PR \#419 - @monkeysecurity - Auditor will now fix any issues that are not attached to an AuditorSetting.
-   PR NONE - @monkeysecurity - Item View no longer returns revision configuration bodies. Should improve UI for items with many revisions.
-   PR NONE - @monkeysecurity - Fixing bug where SSO arguments weren't passed along for branded sso. (Where the name is not google or ping or onelogin)
-   PR \#476 - @markofu - Update aws\_accounts.json to add Canada and Ohio regions.
-   PR NONE - @monkeysecurity - Fixing manage.py::amazon\_accounts() to use new AccountType and adding delete\_unjustified\_issues().
-   PR \#480 - @monkeysecurity - Making Gunicorn an optional import to help support dev on Windows.
-   PR \#481 - @monkeysecurity - Fixing a couple dart warnings.
-   PR \#482 - @monkeysecurity - Replacing Flask-Security with Flask-Security-Fork.
-   PR \#483 - @monkeysecurity - issue \#477 - Fixes IAM User Auditor login\_profile check.
-   PR \#484 - @monkeysecurity - Bumping Jinja2 to \>=2.8.1
-   PR \#485 - @robertoriv - New IAM Role Auditor feature - Check for unknown cross account assumerole.
-   PR \#487 - @hyperbolist - issue \#486 - Upgrade setuptools in Dockerfile.
-   PR \#489 - @monkeysecurity - issue \#251 - Fix IAM SSL Auditor regression. Issue should be raised if we cannot obtain cert issuer.
-   PR \#490 - @monkeysecurity - issue \#421 - Adding ephemeral field to RDS DB issue.
-   PR \#491 - @monkeysecurity - Adding new RDS DB Cluster ephemeral field.
-   PR \#492 - @monkeysecurity - issue \#466 - Updating S3 Auditor to use the ARN class.
-   PR NONE - @monkeysecurity - Fixing typo in dart files.
-   PR \#495 - @monkeysecurity - issue \#494 - Refactoring to work with the new Flask-WTF.
-   PR \#493 - @monkeysecurity - Windows 10 Development instructions.
-   PR NONE - @monkeysecurity - issue \#496 - Bumping CloudAux to \>=1.0.7 to fix IAM User UploadDate field JSON serialization error.

Important Notes:

-   New permissions required:  
    -   s3:getaccelerateconfiguration
    -   s3:getbucketcors
    -   s3:getbucketnotification
    -   s3:getbucketwebsite
    -   s3:getreplicationconfiguration
    -   s3:getanalyticsconfiguration
    -   s3:getmetricsconfiguration
    -   s3:getinventoryconfiguration
    -   route53domains:getdomaindetail
    -   cloudtrail:gettrailstatus

Contributors:

-   @zollman
-   @robertoriv
-   @hyperbolist
-   @markofu
-   @AngeloCiffa
-   @jnbnyc
-   @crruthe
-   @nagwww
-   @mikegrima
-   @monkeysecurity

v0.7.0 (2016-09-21)
-------------------

-   PR \#410/\#405 - @zollman - Custom Watcher/Auditor Support. (Dynamic Loading)
-   PR \#412 - @llange - Google SSO Fixes
-   PR \#409 - @kyelberry - Fixed Report URLs in UI.
-   PR \#413 - @markofu - Better handle IAM SSL certificates that we cannot parse.
-   PR \#411 - @zollman - Many, many new watchers and auditors.

New Watchers:

> -   CloudTrail
> -   AWSConfig
> -   AWSConfigRecorder
> -   DirectConnect::Connection
> -   EC2::EbsSnapshot
> -   EC2::EbsVolume
> -   EC2::Image
> -   EC2::Instance
> -   ENI
> -   KMS::Grant
> -   KMS::Key
> -   Lambda
> -   RDS::ClusterSnapshot
> -   RDS::DBCluster
> -   RDS::DBInstace
> -   RDS::Snapshot
> -   RDS::SubnetGroup
> -   Route53
> -   Route53Domains
> -   TrustedAdvisor
> -   VPC::DHCP
> -   VPC::Endpoint
> -   VPC::FlowLog
> -   VPC::NatGateway
> -   VPC::NetworkACL
> -   VPC::Peering

Important Notes:

-   New permissions required:  
    -   cloudtrail:describetrails
    -   config:describeconfigrules
    -   config:describeconfigurationrecorders
    -   directconnect:describeconnections
    -   ec2:describeflowlogs
    -   ec2:describeimages
    -   ec2:describenatgateways
    -   ec2:describenetworkacls
    -   ec2:describenetworkinterfaces
    -   ec2:describesnapshots
    -   ec2:describevolumes
    -   ec2:describevpcendpoints
    -   ec2:describevpcpeeringconnections,
    -   iam:getaccesskeylastused
    -   iam:listattachedgrouppolicies
    -   iam:listattacheduserpolicies
    -   lambda:listfunctions
    -   rds:describedbclusters
    -   rds:describedbclustersnapshots
    -   rds:describedbinstances
    -   rds:describedbsnapshots
    -   rds:describedbsubnetgroups
    -   redshift:describeclusters
    -   route53domains:listdomains

Contributors:

-   @zollman
-   @kyleberry
-   @llange
-   @markofu
-   @monkeysecurity

v0.6.0 (2016-08-29)
-------------------

-   issue \#292 - PR \#332 - Add ephemeral sections to the redshift watcher
-   PR \#338 - Added access key last used to IAM Users.
-   Added an IAM User auditor check to look for access keys without use in past 90 days.
-   PR \#334 - @alexcline - Route53 watcher and auditor. (Updated to use botor in PR \#343)
-   Logo updated. Weapon replaced with banana. Expect more logo changes soon.
-   PR \#345 - Ephemeral changes now update the latest revision. Revisions now have a date\_last\_ephemeral\_change column as well as a date\_created column.
-   PR \#349 - @mikegrima - Install documentation updates
-   PR \#354 - Feature/SSO (YAY)
-   PR \#365 - @alexcline - Added ACM (Amazon Certificate Manager) watcher/auditor
-   PR \#358/\#370 - @alexcline - Alex cline feature/kms
-   Updated Dart/Angular dart versions.
-   PR \#362 - @crruthe - Changed to dictConfig logging format
-   PR \#372 - @ollytheninja - SQS principal bugfix
-   PR \#379 - @bunjiboys - Adding Mumbai region
-   PR \#380 - @bunjiboys - Adding Mumbai ELB Log AWS Account info
-   PR \#381 - @ollytheninja - Adding tags to the S3 watcher
-   Boto updates
-   PR \#376 - Adding item.arn field. Adding item.latest\_revision\_complete\_hash and item.latest\_revision\_durable\_hash. These are for the bananapeel rearchitecture.
-   PR \#386 - Shortening sessions from default value to 60 minutes. Setting Cookie HTTPONLY and SECURE flags.
-   PR \#389 - Adding CloudTrail table, linked to itemrevision. (To be used by bananapeel rearchitecture.)
-   PR \#390 - @ollytheninja - Adding export CSV button.
-   PR \#394 - @mikegrima - Saving exceptions to database table
-   PR \#402 - issue \#401 - Adding new ELB Reference Policy ELBSecurityPolicy-2016-08

Hotfixes:

-   Upgraded Cryptography to 1.3.1
-   Updated docs to use sudo -E when calling manage.py amazon\_accounts.
-   Updated the @record\_exception decorator to allow the region to be overwritten. (Useful for region-less technology that likes to be recorded in the "universal" region.)
-   issue \#331 - IAMSSL watcher failed on elliptic curve certs

Important Notes:

-   Route53 IgnoreList entries may match zone name or recordset name.
-   Checkout the new log configuration format from PR \#362. You may want to update your config.py.
-   New permissions required:  
    -   "acm:ListCertificates",
    -   "acm:DescribeCertificate",
    -   "kms:DescribeKey",
    -   "kms:GetKeyPolicy",
    -   "kms:ListKeys",
    -   "kms:ListAliases",
    -   "kms:ListGrants",
    -   "kms:ListKeyPolicies",
    -   "s3:GetBucketTagging"

-   Some dependencies have been updated (cryptography, boto, boto3, botocore, botor, pyjwt). Please re-run python setup.py install.
-   Please add the following lines to your config.py for more time-limited sessions:

~~~~ {.sourceCode .python}
PERMANENT_SESSION_LIFETIME=timedelta(minutes=60)   # Will logout users after period of inactivity.
SESSION_REFRESH_EACH_REQUEST=True
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
PREFERRED_URL_SCHEME='https'

REMEMBER_COOKIE_DURATION=timedelta(minutes=60)  # Can make longer if  you want remember_me to be useful
REMEMBER_COOKIE_SECURE=True
REMEMBER_COOKIE_HTTPONLY=True
~~~~

Contributors:

-   @alexcline
-   @crruthe
-   @ollytheninja
-   @bunjiboys
-   @mikegrima
-   @monkeysecurity

v0.5.0 (2016-04-26)
-------------------

-   PR \#286 - bunjiboys - Added Seoul region AWS Account IDs to import scripts
-   PR \#291 - sbasgall - Corrected ignore\_list.py variable names and help strings
-   PR \#284 - mikegrima - Fixed cross-account root reporting for ES service (Issue \#283)
-   PR \#293 - mikegrima - Updated quickstart documentation to remove permission wildcards (Issue \#287)
-   PR \#301 - monkeysecurity - iamrole watcher can now handle many more roles (1000+) and no longer times out.
-   PR \#316 - DenverJ - Handle database exceptions by cleaning up session.
-   PR \#289 - delikat - Persist custom role names on account creation
-   PR \#321 - monkeysecurity - Item List and Item View will no longer display disabled issues.
-   PR \#322 (PR \#308) - llange - Ability to add AWS owned managed policies to ignore list by ARN (Issue \#148)
-   PR \#323 - snixon - Breaks check\_securitygroup\_any into ingress and egress (Issue \#239)
-   PR \#309 - DenverJ - Significant database query optimizations by tuning itemrevision retrievals
-   PR \#324 - mikegrima - Handling invalid ARNs more consistently between watchers (Issue \#248)
-   PR \#317 - ollytheninja - Add Role Based Access Control
-   PR \#327 - monkeysecurity - Added Flask-Security's SECURITY\_TRACKABLE to backend and UI
-   PR \#328 - monkeysecurity - Added ability to parse AWS service "ARNs" like events.amazonaws.com as well as ARNS that use \* for the account number like arn:aws:s3:​\*:\*​:some-s3-bucket
-   PR \#314 - pdbogen - Update Logging to have the ability to log to stdout, useful for dockerizing.

Hotfixes:

-   s3\_acl\_compare\_lowercase: AWS now returns S3 ACLs with a lowercased owner. security\_monkey now does a case insensitive compare
-   longer\_resource\_ids. Updating DB to handle longer AWS resource IDs: <https://aws.amazon.com/blogs/aws/theyre-here-longer-ec2-resource-ids-now-available/>
-   Removed requests from requirements.txt/setup.py as it was pinned to a very old version and not directly required (Issue \#312)
-   arn\_condition\_awssourcearn\_can\_be\_list. Updated security\_monkey to be able to handle a list of ARNS in a policy condition.
-   ignore\_list\_fails\_on\_empty\_string: security\_monkey now properly handles an ignorelist entry containing a prefix string of length 0.
-   protocol\_sslv2\_deprecation: AWS stopped returning whether an ELB listener supported SSLv2. Fixed security\_monkey to handle the new format correctly.

Important Notes:

-   security\_monkey IAM roles now require a new permission: iam:listattachedrolepolicies
-   Your security\_monkey config file should contain a new flag: SECURITY\_TRACKABLE = True
-   You'll need to rerun python setup.py install to obtain the new dependencies.

Contributors:

-   @bunjiboys
-   @sbasgall
-   @mikegrima
-   @DenverJ
-   @delikat
-   @snixon
-   @ollytheninja
-   @pdbogen
-   @monkeysecurity

v0.4.1 (2015-12-22)
-------------------

-   PR \#269 - mikegrima - TravisCI now ensures that dart builds.
-   PR \#270 - monkeysecurity - Refactored sts\_connect to dynamically import boto resources.
-   PR \#271 - OllyTheNinja-Xero - Fixed indentation mistake in auditor.py
-   PR \#275 - AlexCline - Added elb logging to ELB watcher and auditor.
-   PR \#279 - mikegrima - Added ElasticSearch Watcher and Auditor (with tests).
-   PR \#280 - monkeysecurity - PolicyDiff better handling of changes to primitives (like ints) in dictionay values and added explicit escaping instead of relying on Angular.
-   PR \#282 - mikegrima - Documentation Fixes to configuration.rst and quickstart.rst adding es: permissions and other fixes.

Hotfixes:

-   Added OSSMETADATA file to master/develop for internal Netflix tracking.

Contributors:

-   @mikegrima
-   @monkeysecurity
-   @OllyTheNinja-Xero
-   @AlexCline

v0.4.0 (2015-11-20)
-------------------

-   PR \#228 - jeremy-h - IAM check misses '\*' when found within a list. (Issue \#223)
-   PR \#230 - markofu - New error and echo functions to simplify code for scripts/secmonkey\_auto\_install.sh
-   PR \#233 - mikegrima - Write tests for security\_monkey.common.ARN (Issue \#222)
-   PR \#238 - monkeysecurity - Refactoring \_check\_rfc\_1918 and improving VPC ELB Internet Accessible Check
-   PR \#241 - bunjiboys - Seed Amazon owned AWS accounts (Issue \#169)
-   PR \#243 - mikegrima - Fix for underscores not being detected in SNS watcher. (Issue \#240)
-   PR \#244 - mikegrima - Setup TravisCI (Issue \#227)
-   PR \#250 - OllyTheNinja-Xero - upgrade deprecated botocore calls in ELB watcher (Issue \#249)
-   PR \#256 - mikegrima - Latest Boto3/botocore versions (Issue \#254)
-   PR \#261 - bunjiboys - Add ec2:DescribeInstances to quickstart role documentation (Issue \#260)
-   PR \#263 - monkeysecurity - Updating docs/scripts to pin to dart 1.12.2-1 (Issue \#259)
-   PR \#265 - monkeysecurity - Remove ratelimiting max attempts, wrap ELB watcher with try/except/continue

Hotfixes:

-   Issue \#235 - OllyTheNinja-Xero - SNS Auditor - local variable 'entry' referenced before assignment

Contributors:

-   @jeremy-h
-   @mark-fu
-   @mikegrima
-   @bunjiboys
-   @OllyTheNinja-Xero
-   @monkeysecurity

v0.3.9 (2015-10-08)
-------------------

-   PR \#212 - bunjiboys - Make email failures warnings instead of debug messages
-   PR \#203 - markofu - Added license to secmonkey\_auto\_install.sh.
-   PR \#207 - cbarrac - Updated dependencies and dart installation for secmonkey\_auto\_install.sh
-   PR \#209 - mikegrima - Make SNS Ignorelist use name instead of ARN.
-   PR \#213 - Qmando - Added more exception handling to the S3 watcher.
-   PR \#215 - Dklotz-Circle - Added egress rules to the security group watcher.
-   monkeysecurity - Updated quickstart.rst IAM policy to remove wildcards and include redshift permissions.
-   PR \#218 - monkeysecurity - Added exception handling to the S3 bucket.get\_location API call.
-   PR \#221 - Qmando - Retry on AWS API error when slurping ELBs.
-   monkeysecurity - Updated cryptography package from 1.0 to 1.0.2 for easier installation under OS X El Capitan.

Hotfixes:

-   Updated quickstart.rst and secmonkey\_auto\_install.sh to remove swig/python-m2crypto and add libffi-dev
-   Issue \#220 - SQS Auditor not correctly parsing ARNs, halting security\_monkey. Fixed by abstracting ARN parsing into a new class (security\_monkey.common.arn). Updated the SNS Auditor to also use this new class.

Contributors:

-   bunjiboys
-   markofu
-   cbarrac
-   mikegrima
-   Qmando
-   Dklotz-Circle
-   monkeysecurity

v0.3.8 (2015-08-28)
-------------------

-   PR \#165 - echiu64 - S3 watcher now tracking S3 Logging Configuration.
-   None - monkeysecurity - Certs with an invalid issuer now flagged.
-   PR \#177 - DenverJ -Added new SQS Auditor.
-   PR \#188 - kevgliss - Removed dependency on M2Crypto/Swig and replaced with Cryptography.
-   PR \#164 - Qmando - URL encoding issue with certain searches containing spaces corrected.
-   None - monkeysecurity - Fixed issue where corrected issues were not removed.
-   PR \#198 - monkeysecurity - Adding ability to select up to four items or revisions to be compared.
-   PR \#194 \#195 - bunjiboys - SECURITY\_TEAM\_EMAIL should accept not only a list, but also a string or tuple.
-   PR \#180 \#181 \#190 \#191 \#192 \#193 - cbarrac - A number of udpates and fixes for the bash installer. (scripts/secmonkey\_auto\_installer.sh)
-   PR \#176 \#178 - mikegrima - Updated documentation for contributors on OS X and Ubuntu to use Webstorm instead of the Dart Editor.

Contributors:

-   Qmando
-   echiu64
-   DenverJ
-   cbarrac
-   kevgliss
-   mikegrima
-   monkeysecurity

v0.3.7 (2015-07-20)
-------------------

-   PR \#122 - Qmando - Jira Sync. Quentin from Yelp added Jira Integration.
-   PR \#147 - echiu64 - Added colors to audit emails and added missing justifications back into emails.
-   PR \#150 - echiu64 - Fixed a missing comma from setup.py
-   PR \#155 - echiu64 - Fixed a previous merge issue where \_audit\_changes() was looking for a Monitor instance instead of an list of Auditors.
-   Issue \#154 - monkeysecurity - Added support for ELB Reference Policy 2015-05.
-   None - monkeysecurity - Added db.session.refresh(...) where appropriate in a few API views to replace some very ugly code.
-   Issue \#133 - lucab - Upgraded Flask-RESTful from v0.2.5 to v0.3.3 to fix an issue where request arguments were being persisted as the string "None" when they should have remained the javascript literal null.
-   PR \#120 - lucab - Add custom role\_name field for each account to replace the previously hardcoded 'SecurityMonkey' role name.
-   PR \#120 - gene1wood - Add support for the custom role\_name into manage.py.
-   PR \#161 - Asbjorn Kjaer - Increase s3\_name from 32 characters to 64 characters to avoid errors or truncation where s3\_name is longer.
-   None - monkeysecurity - Set the 'defer' (lazy-load) attribute for the JSON config column on the ItemRevision table. This speeds up the web API in a number of places.

Hotfixes:

-   Issue \#149 - Python scoping issue where managed policies attached to more than one entity would cause an error.
-   Issue \#152 - SNS topics were being saved by ARN instead of by name, causing exceptions for very long names.
-   Issue \#141 - Setup cascading deletes on the Account table to prevent the error which occured when trying to delete an account with items and users attached.

Contributors:

-   Qmando
-   echiu64
-   lucab
-   gene1wood
-   Asbjorn Kjaer (akjaer)
-   monkeysecurity

v0.3.6 (2015-04-09)
-------------------

-   Changes to issue score in code will now cause all existing issues to be re-scored in the database.
-   A new configuration parameter called SECURITYGROUP\_INSTANCE\_DETAIL can now be set to:  
    -   "FULL": Security Groups will display each instances, and all instance tags, that are associated with the security group.
    -   "SUMMARY": Security Groups will display the number of instances attached to the security group.
    -   "NONE": Security Groups will not retrieve any data about instances attached to a security group.
    -   If SECURITY\_GROUP\_INSTANCE\_DETAIL is set to "FULL" or "SUMMARY", empty security groups audit issues will have their score set to zero.
    -   For accounts with many thousands of instances, it is advised to set this to "NONE" as the AWS API's do not respond in a timely manner with that many instances.

-   Each watcher can be set to run at a different interval in code. We will want to move this to be a UI setting.
-   Watchers may specify a list of ephemeral paths. Security\_monkey will not send out change alerts for items in the ephemeral section. This is a good place for metadata that is often changing like the number of instances attached to a security\_group or the number of remaining IP addresses in a VPC subnet.

Contributors:

-   lucab
-   monkeysecurity

v0.3.5 (2015-03-28)
-------------------

-   Adding policy minimizer & expander to the revision component
-   Adding tracking of instance profiles attached to a role
-   Adding marker/pagination code to redshift.describe\_clusters()
-   Adding pagination to IAM User get\_all\_user\_policies, get\_all\_access\_keys, get\_all\_mfa\_devices, get\_all\_signing\_certs
-   Typo & minor corrections on postgres commands
-   CLI command to save your current configurations to a JSON file for backup
-   added a VPC watcher
-   Adding DHCP Options and Internet Gateways to the VPC Watcher
-   Adding a subnet watcher. Fixing the VPC watcher with deep\_dict
-   Adding the vpc route\_table watcher
-   Removing subnet remaining IP field until ephemeral section is merged in
-   Adding IAM Managed Policies
-   Typo & minor corrections on postgres commands in documentation
-   Adds ELBSecurityPolicy-2015-03. Moves export grade ciphers to their own section and alerts on FREAK vuln.
-   Provides context on refpol 2015-03 vs 2015-02.
-   Adding a Managed Policies Auditor
-   Added Manged Policy tracking to the IAM users, groups, and roles

Summary of new watchers:

-   vpc  
    -   DHCP Options
    -   Internet Gateways

-   subnet
-   routetable
-   managed policies

Summary of new Auditors or audit checks:

-   managed policies
-   New reference policy 2015-03 for ELB listeners.
-   New alerts for FREAK vulnerable ciphers.

Contributors:

-   markofu
-   monkeysecurity

v0.3.4 (2015-2-19)
------------------

-   Merged in a new AuditorSettings tab created by Qmando at Yelp enabling you to disable audit checks with per-account granularity.
-   security\_monkey is now CSP compliant.
-   security\_monkey has removed all shadow-DOM components. Also removed webcomponents.js and dart\_support.js, as they were not CSP compliant.
-   security\_monkey now advises users to enable standard security headers following headers:

~~~~ {.sourceCode .python}
X-Content-Type-Options "nosniff";
X-XSS-Protection "1; mode=block";
X-Frame-Options "SAMEORIGIN";
Strict-Transport-Security "max-age=631138519";
Content-Security-Policy "default-src 'self'; font-src 'self' https://fonts.gstatic.com; script-src 'self' https://ajax.googleapis.com; style-src 'self' https://fonts.googleapis.com;"
~~~~

-   security\_monkey now has XSRF protection against all DELETE, POST, PUT, and PATCH calls.
-   Updated the ELB Auditor to be aware of the ELBSecurityPolicy-2015-02 reference policy.

Contributers:

-   Qmando
-   monkeysecurity

v0.3.3 (2015-2-3)
-----------------

-   Added MirorsUsed() to my dart code to reduce compiled javascript size.
-   Added support for non-chrome browsers by importing webcomponents.js and dart\_support.js
-   Upgraded to Angulardart 1.1.0 and Angular-dart.ui 0.6.3

v0.3.2 (2015-1-20)
------------------

-   A bug has been corrected where IAM Groups with \> 100 members or policies would be truncated.
-   The web UI has been updated to use AngularDart 1.0.0. Significantly smaller javascript size.

v0.3.1 (2015-1-11)
------------------

-   Change emails again show issues and justifications.
-   Change emails now use jinja templating.
-   Fixed an issue where issue justifications would disappear when the item was changed.
-   Merged a pull request from github user jijojv to start the scheduler at launch instead of waiting 15 minutes.

v0.3.0 (2014-12-19)
-------------------

-   Add localhost to CORS for development.
-   Big refactor adding monitors. Adding new watchers/auditors is now much simpler.
-   Return to the current URL after authenticating.
-   Added SES\_REGION config. Now you can send email out of regions other than us-east-1.
-   Changing default log location to /var/log/security\_monkey.
-   Docs now have cleaner nginx.conf.
-   Add M2Crypto to get a number of new iamssl fields.
-   Added favicon.

new watchers:

-   eip
-   redshift
-   ses

enhanced watchers:

-   iamssl - new fields from m2crypto
-   elb - new listener policies from botocore
-   sns - added sns subscriptions
-   s3 - now tracks lifecycle rules

new auditors:

-   redshift - checks for non-vpc deployment.
-   ses - checks for verified identities

enhanced auditors:

-   iamssl - cert size, signature hashing algorithm, upcoming expiration, heartbleed
-   elb - check reference policy and certain custom policy fields

hotfixes:

-   Fixed issue \#12 - Deleting account results in foreign key constraint.
-   Added missing alembic script for the ignorelist.
-   Various minor documentation updates.
-   API server now respects --bind parameter. (Required for the docker image).
-   SES connection in utils.py is now surrounded in a try/except.
-   FlaskSecurity upgraded to latest.

Contributers:

-   ivanlei
-   lucab
-   yograterol
-   monkeysecurity

v0.2.0 (2014-10-31)
-------------------

Changes in the Web UI:

-   Dart: Dates are now displayed in your local timezone.
-   Dart: Added Item-level comments.
-   Dart: Added the ability to bulk-justify issues from the Issues Table view. This uses the AngularDartUI Modal Component.
-   Dart: Added better messaging around the settings for adding an account. This closes issue \#38. This uses the AngularDartUI tooltip component.
-   Bug Fix: Colors in the Item table now correctly represent the justification status.
-   Dart: Added AngularUI Tabs to select between diff and current configuration display.
-   Dart: Added a timer-based auto-refresh so SM can be used as a dashboard.
-   Dart: Replaced a number of custom http services with Victor Savkin's Hammock library.
    - More than 965 lines of code removed after using Hammock.
-   Dart: Replaced custom pagination code with AngularDartUI's Pagination Component.
    -   IssueTable
    -   RevisionTable
    -   ItemTable

    - AccountSettingsTable
-   Dart: Network CIDR whitelist is now configured in the web UI under settings.
-   Dart: Object Ignorelist is now configured in the web UI under settings.
-   Created a new PaginatedTable parent class for all components that wish to display paginated data. This table works with AngularDart's Pagination Component and also provides the ability to change the number of items displayed on each page.
-   Dart: Added ng\_infinite\_scroll to the item\_detail\_view for loading revisions
-   Dart: Moved a number of components from being their own libraries to being `` `part of ``\` the security\_monkey library.
-   Dart: Replaced the last controller (UsernameController) with a Component to prepare for AngularDart 1.0.0
-   Dart: Style - Renamed library from SecurityMonkey to security\_monkey to follow the dart style guide. Refactored much of main.dart into lib/security\_monkey.dart to try and mimic the cleaner design of the new angular sample app: <https://github.com/vsavkin/angulardart-sample-app>

Changes in the core product:

-   Updated API endpoints to better follow REST architecture.
-   Added table for NetworkWhitelist.
-   Added rest API endpoints for NetworkWhitelist.
-   Added Alembic migration script to add the new NetworkWhitelist table to the DB.
-   Added table for IgnoreList.
-   Added rest API endpoints for Ignorelist.
-   Added Alembic migration script to add the new IgnoreList table to the DB.
-   Added check for rfc-1918 CIDRs in non-VPC security groups.
-   Saving IAMSSL Certs by cert name instead of cert ID
-   Marking VPC RDS Security Groups with their VPC ID
-   Supports Paginated Boto access for RDS Security Groups.
-   Added alert for non-VPC RDS SG's containing RFC-1918 CIDRs
-   Added check for IAM USER AKEY rotation
-   Added check for IAM USER with login profile (console access) And Access Keys (API Access)
-   Added an ELB Auditor with a check for internet-facing ELB.
-   Added check for security groups with large port ranges.

v0.1.2 (2014-08-11)
-------------------

Changes in the Web UI:

-   Dart: Removed Shadow DOM dependency and set version bounds in pubspec.yaml.
-   Dart: Replaced package:js with dart:js.
-   Dart: Added the Angular Pub Transformer.

Changes in the core product:

-   Added AWS Rate Limiting Protection with exponential backoff code.
-   Added instructions to get a local development environment setup for contributing to security\_monkey.
-   Added support for boto's new ELB pagination. The pull request to boto and to security\_monkey came from Kevin Glisson.
-   Bug fix: Security Group Audit Issues now include the port the issue was reported on.

These were already in master, but weren't tied to a new release:

-   Bug fix: Supervisor script now sets SECURITY\_MONKEY\_SETTINGS envvar for the API server whereas it only previously set the envvar for the scheduler. This came from a pull request from parabolic.
-   Bug fix: Audit reports will only be sent if there are issues to report on.
-   Bug fix: Daily Audit Email setting (ALL/NONE/ISSUES) is now respected.
-   Bug fix: Command Line Auditor Command Arguments are now coerced into being booleans.
-   Quickstart Guide now instructs user to setup the web UI on SSL.
-   Various Smaller Bug Fixes.

v0.1.1 (2014-06-30)
-------------------

Initial release of Security Monkey!
