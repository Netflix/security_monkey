Security Monkey for GitHub Organizations
=====================

As part of a 2017 Hack Day project, we added Security Monkey watching and auditing support for Github Organizations,
repositories, and teams.

Before reviewing the instructions for this, we highly suggest reviewing our [quickstart guide](quickstart.md) for AWS and GCP,
as well as the [userguide](userguide.md).

What does this do?
---------------
This works similarly to how AWS and GCP support works in that it monitors resources in organizations and
their changes over time.

This also includes some auditors to catch possible issues, such as organization members without 2FA enabled.

RATE LIMITS, RATE LIMITS, RATE LI...Sorry, you have reached the limit...
-------
A major caveat is that GitHub has very strict API rate limits. This is based on total number of requests
per hour (5000). As such, you can reach this limit if you want to monitor multiple organizations
with many repos.

Rate limits affect the GitHub user(s) performing the API calls. Please be aware that if the user reaches the limit,
it will not be able to perform other tasks until the next hour. This can be a problem if you are using the same bot account's
credentials for other tasks and automation.

For more details on API limits and GitHub, [please review GitHub's documentation](https://developer.github.com/v3/rate_limit/).

Installation Instructions
---------------
Please follow the instructions in the [quickstart guide](quickstart.md) for installation. It is recommended that you
not audit both AWS/GCP and GitHub with the same Security Monkey installation.

If you are standing up a standalone Security Monkey for GitHub installation, then you must follow all of the standard
installation instructions with the exception of IAM. SM-GH will not require any special IAM permissions. All other
installation instructions are still valid.

Access Keys and Permissions
---------------
For this to work, you will need:
1. At least 1 GitHub organization
1. An organization member that has `Admin` privileges on all repositories within the organization, or an `Owner` of the organization. Please note: these are powerful permissions, so please keep this account locked down.
1. A personal access token for the organization member.

For obtaining a personal access token, please review GitHub's [documentation here](https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/).

You will need to provide the following scopes for the token:
`repo, read:org, read:public_key, user, read:gpg_key`
![scopes](images/github_scopes.png)

In addition to the scopes, the user must also be placed on a team with at least read-only access to all repositories
within the organization.

Preparing the Credentials
--------------
Security Monkey reads the credentials via a Python `dict` -- or JSON file.

The format is like so:
```
{
  "OrganizationNameHere": "personal access token with access to org here.",
  "SecondOrganizationNameHere": "personal access token with access to org here",
  ...
}

```

You can place this in the Security Monkey `env-config/ConfigYouAreUsing.py`. If so, you must add a field named `GITHUB_CREDENTIALS` set
to the credentials `dict`:
```
GITHUB_CREDENTIALS = {
  "OrganizationNameHere": "personal access token with access to org here.",
  "SecondOrganizationNameHere": "personal access token with access to org here"
}
```

Alternatively, you can save the `dict` as a JSON file and have Security Monkey load that file for a given account. More on this below.

Add GitHub Organizations to Monitor
------------------------
You can add organizations via the UI or the CLI.

```
usage: monkey add_account_github [-h] -n NAME [--thirdparty] [--active]
                                 [--notes NOTES] --id IDENTIFIER
                                 [--update-existing]
                                 [--access_token_file ACCESS_TOKEN_FILE]
```

The fields (also presented in the UI) are the following:
1. `-n NAME` - This is the name of the account that You want Security Monkey to refer to your organization as. This could either be the full name
               of the org, or an alias to it. This is unique.
1. `--active` - Must be present for Security Monkey to scan and check resources within the org.
1. `--id IDENTIFIER` - This is the complete name that GitHub has for the organization. This is unique and must match the name of the organization on GitHub.
1. `--access_token_file ACCESS_TOKEN_FILE` - This is optional. If you added the GitHub credentials `dict` to the Security Monkey configuration file, then you
    don't need to specify this. Otherwise, you can specify the full path to a JSON file with the credentials as formatted as above.
1. `--notes NOTES` - OPTIONAL: Some notes that you may wish to add to the account for referencing.

__NOTE: Don't forget to restart the scheduler after adding new accounts!__ For more information, please read the [quickstart guide](quickstart.md).
