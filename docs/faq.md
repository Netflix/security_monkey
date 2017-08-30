FAQ and Troubleshooting
=======================


Error: Too many open files
--------------------------
Too many open files' [in /usr/local/src/security_monkey/security_monkey/exceptions.py:68]

Solution: Try increasing the limit for open file handlers

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

Reference:[Raising the maximum number of file descriptors](https://underyx.me/2015/05/18/raising-the-maximum-number-of-file-descriptors)

Note: Above steps were tested on Ubuntu 16.10