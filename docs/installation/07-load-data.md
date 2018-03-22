Logging into the UI
-------------------

You should now be able to reach your server

![image](../images/resized_login_page-1.png)

Loading Data into Security Monkey
--------------------------------
To initially get data into Security Monkey, you can run the `monkey find_changes` command. This will go through
all your configured accounts in Security Monkey, fetch details about the accounts, store them into the database,
and then audit the items for any issues. 

The `find_changes` command can be further scoped to account and technology with the `-a account` and `-m technology` parameters.

*Note:* This is good for loading some initial data to play around with, however, you will want to configure jobs to automatically
scan your environment periodically for changes.  Please read the next section for details.

🚨 Important 🚨 - Autostarting and Fetching Data
--------------------------------
At this point Security Monkey is set to manually run. However, we need to ensure that it is always running and automatically
fetching data from your environment.

Please review the next section titled [Autostarting Security Monkey](../autostarting.md) for details. Please note, this section
is very important and involved, so please pay close attention to the details.