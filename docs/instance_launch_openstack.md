Launch an OpenStack instance
============================

Orchestrate an instance (via Horizon/Heat/APIs). Below are some guidelines. Your cloud setup, conventions, and policies will dictate specifics.

-   **Source**: Ubuntu LTS (14.04 or 16.04) source
-   **Machine Type**: m1.medium or equivalent (3.75GB RAM minimum)
-   **Security Group**: Allow appropriately restricted ingress HTTPS and SSH. For egress, allow access to the OpenStack service API endpoints (in Horizon, found under API Access details) and for the initial Security Monkey installation you will access to the Internet/proxy.


Connecting to your new instance:
--------------------------------

We will connect to the new instance over ssh:

    $ ssh -i <PRIVATE_KEY> -l ubuntu <IP_ADDRESS>

Replace the PRIVATE_KEY parameter with the private key for your keypair assigned in instance creation
Replace the IP_ADDRESS with the IP address of your instance (public or floating ip, depending on network assignment)


Next:
-----

- [Back to the Quickstart](quickstart.md#install-security-monkey-on-your-instance)
