Launch an AWS Instance
======================

Netflix monitors dozens AWS accounts easily on a single m3.large instance. For this guide, we will launch a m1.small.

In the console, start the process to launch a new Ubuntu instance. The screenshot below shows EC2 classic, but you can also launch this in external VPC.:

![image](images/resized_ubuntu.png)

Select an m1.small and select "Next: Configure Instance Details".

**Note: Do not select "Review and Launch". We need to launch this instance in a specific role.**

![image](images/resized_select_ec2_instance.png)

Under "IAM Role", select SecurityMonkeyInstanceProfile:

![image](images/resized_launch_instance_with_role.png)

You may now launch the new instance. Please take note of the "Public DNS" entry. We will need that later when configuring security monkey.

![image](images/resized_launched_sm.png)

Now may also be a good time to edit the "launch-wizard-1" security group to restrict access to your IP. Make sure you leave TCP 22 open for ssh and TCP 443 for HTTPS.

Keypair
-------

You may be prompted to download a keypair. You should protect this keypair; it is used to provide ssh access to the new instance. Put it in a safe place. You will need to change the permissions on the keypair to 400:

    $ chmod 400 SecurityMonkeyKeypair.pem

Connecting to your new instance:
--------------------------------

We will connect to the new instance over ssh:

    $ ssh -i SecurityMonkeyKeyPair.pem -l ubuntu <PUBLIC_IP_ADDRESS>

Replace the last parameter (\<PUBLIC\_IP\_ADDRESS\>) with the Public IP of your instance.

Next:
-----

- [Back to the Quickstart](quickstart.md#install-security-monkey-on-your-instance)