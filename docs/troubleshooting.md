Troubleshooting Guide
==========

This is a doc to outline some of the most common issues that users have encountered and their solutions. We very much welcome
Pull-Requests to this doc for items to help other Security Monkey users.

Existing Resources
------------
In general, if you are encountering issues, please review the GitHub issues (open and closed) to see if anyone else has
already experienced the issue. We often find that most issues users experience have already been solved.

Also, please review the [quickstart guide](https://github.com/Netflix/security_monkey/blob/develop/docs/quickstart.md). This will likely help uncover the issue you may be experiencing.


Enable Debug Logging
---------------
Logs are very useful for debugging issues. Enabling debug logging will help provide additional details on what may be breaking.
To do this, you need to modify the configuration Python file that is in use by Security Monkey. Namely, you need to modify the `LOG_CFG` section.
You need to set all `level` settings to `DEBUG`. Save the file, and then reload Security Monkey.


Common Issues
-----------
This is a list of common issues and their resolutions.  

1. **No data is loading**
   
    This is perhaps the number 1 issue users encounter. This can be caused for a number of reasons:
      - Insufficient permissions for the Security Monkey IAM Roles.
        **Solution**: [Follow the IAM instructions](https://github.com/Netflix/security_monkey/blob/develop/docs/quickstart.md#account-types) for the given technology in question and ensure that the proper permissions are in place.
        
      - I'm seeing: `Unable to locate credentials` errors.
        **Solution**: If you are running in AWS, you will need to ensure that you launch all of your Security Monkey instances with
        the `SecurityMonkeyInstanceProfile`. [Please follow the IAM instructions](iam_aws.md)
        and the `Launch a new Instance` section of the [AWS instance launching documentation](instance_launch_aws.md).
     
      - Scheduler and workers are not functioning properly.
        **Solution**: Follow the [autostarting guide](https://github.com/Netflix/security_monkey/blob/develop/docs/autostarting.md), and ensure that the following is true:
          - Remember, there should only ever be exactly one scheduler instance running (only 1 celery scheduler process that should ever be running)
          - Security Monkey and the workers have network connectivity to the Redis queue.
          - To track down issues with the scheduler, try running the `monkey find_changes -a ACCOUNT` command to see if items can be fetched. This will help uncover other
            issues that may be relevant.

1. **I'm seeing "Access Denied" errors.**
    
    This is caused by insufficient permissions. **Solution**: [Follow the IAM instructions](https://github.com/Netflix/security_monkey/blob/develop/docs/quickstart.md#account-types) for the given technology in question and ensure that the proper permissions are in place.

1. **Error: Too many open files.** (This is not likely to be as much of a problem in v1.0+ but if you encounter it, then follow the instructions below)
    
    You might see an error along the lines of: `Too many open files' [in /usr/local/src/security_monkey/security_monkey/exceptions.py:68]`

    **Solution:** Try increasing the limit for open file handlers
    
    ```bash
    /etc/security/limits.conf
    *    soft nofile 100000
    *    hard nofile 100000
    
    /etc/pam.d/common-session
    session required pam_limits.so
    
    /etc/pam.d/common-session-noninteractive 
    session required pam_limits.so
    
    /etc/supervisor/supervisord.conf, in the [supervisord] section:
    minfds=100000
    ```
    
    Reference: [Raising the maximum number of file descriptors](https://underyx.me/2015/05/18/raising-the-maximum-number-of-file-descriptors)

 1. **Some accounts are getting data but others aren't.**

    There are many things that can cause this.
      - Make sure that the Scheduler is running properly and not restarting. Check the logs to ensure that things are OK here.
      - Check that the workers are getting tasked and aren't prematurely quitting. Check the logs to ensure that things are OK here.
      - If you are using prioritized schedulers and watchers as documented in the [Tuning the Watchers / Prioritizing](tuneworkers.md) doc,
          make sure that you have provided a `--pidfile` parameter with a `pid` file that is specific to the scheduler and corresponding watcher.
          Otherwise, they will step on each other and fail. One hint that this is happening is if you see multiple workers being tasked to the same
          accounts over and over again.

1. **I am seeing issues that I don't really care about. Can these be ignored?**
    
    **SOLUTION:** Yes. See the [User Guide's](https://github.com/Netflix/security_monkey/blob/develop/docs/userguide.md) section titled: "Disabling auditor checks / overriding scores"
