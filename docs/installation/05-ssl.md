Create an SSL Certificate
-------------------------

For this quickstart guide, we will use a self-signed SSL certificate. In production, you will want to use a certificate that has been signed by a trusted certificate authority.:

    $ cd ~

There are some great instructions for generating a certificate on the Ubuntu website:

[Ubuntu - Create a Self Signed SSL Certificate](https://help.ubuntu.com/14.04/serverguide/certificates-and-security.html)

The last commands you need to run from that tutorial are in the "Installing the Certificate" section:

~~~~ {.sourceCode .bash}
sudo cp server.crt /etc/ssl/certs
sudo cp server.key /etc/ssl/private
~~~~

Once you have finished the instructions at the link above, and these two files are in your /etc/ssl/certs and /etc/ssl/private, you are ready to move on in this guide.

--
### Next step: [Setup Nginx](06-nginx.md)
--