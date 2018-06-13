# Slack Integration w/Security Monkey

---

[Click here to read the slackAPI Documentation](https://api.slack.com/#read_the_docs)

---

### Integration Tutorial for Instances using a Scheduler:

#### Installing the bot on your Security Monkey EC2 instance:

```
cd /usr/local/src/security_monkey
```

```
source venv/bin/activate
```

```
pip install slackclient
```

#### Setting up your "APP" on Slack

[Handy Link to Create a Slackbot App](https://api.slack.com/apps/new)

When prompted to give a App Name you can name it whatever relates to your project (ex: SMSlackBot).
Make sure your App is in the correct development workspace in reference to where you would like it to be present

#### Creating a bot to send/receive the requests:

After creating the application, we need to create a bot user which handles the conversations and messaging between security monkey and slack. Create a new [bot user](https://api.slack.com/bot-users) and then continue by saving the changes.

#### Setting up communication/authentication:

After your new bot is now created with it's username, Click on the "Install App" under the "Settings" section. The button on this page will install the App into our your workspace you selected the app to be in at the start. Once the App is installed, it displays a bot user oauth access token for authentication as the bot user. We want the "Bot User OAuth Access Token", since this is the one that is linked to our bot we just created. Using this key generated we need to add it to our environment on our Security Monkey instance.

The tricky part about this is depending on the Implementation it may either need to be in the scheduler environment, user environment, or "root" environment.

##### a. Scheduler environment (Supervisor/Celery Conf Setup):

```
cd /usr/local/src/security_monkey/supervisor/security_monkey_scheduler.conf
```

```
vi security_monkey_scheduler.conf or nano 
security_monkey_scheduler.conf
```

```
add env location your SLACK_API_TOKEN information to make sure when the supervisor runs that it actually is present in the environment.
```

##### b. User environment (Manual Setup - Ran as user):

```
cd /usr/local/src/security_monkey
```

```
source venv/bin/activate
```

```
export SLACK_API_TOKEN=OAUTH TOKEN HERE
```

##### c. Root environment (Manual Setup - Ran as root):

```
cd /usr/local/src/security_monkey
```

```
source venv/bin/activate
```

```
export SLACK_API_TOKEN=OAUTH TOKEN HERE
```

```
sudo -E bash -c 'echo $SLACK_API_TOKEN'
```
