Launch a GCP instance
=====================

Create an instance running Ubuntu 16.04 LTS using our 'securitymonkey' service account.

Navigate to the [Create Instance page](https://console.developers.google.com/compute/instancesAdd). Fill in the following fields:

-   **Name**: securitymonkey
-   **Zone**: If using GCP Cloud SQL, select the same zone here. [(Zone List)](https://cloud.google.com/compute/docs/regions-zones/regions-zones#available)
-   **Machine Type**: 1vCPU, 3.75GB (minimum; also known as n1-standard-1)
-   **Boot Disk**: Ubuntu 16.04 LTS
-   **Service Account**: securitymonkey (This is provisioned in the [IAM GCP instructions](https://github.com/Netflix/security_monkey/blob/develop/docs/iam_gcp.md).)
-   **Firewall**: Allow HTTPS Traffic

Click the *Create* button to create the instance.

Install gcloud
--------------

If you haven't already, install *gcloud* from the [downloads](https://cloud.google.com/sdk/downloads) page. *gcloud* enables you to administer VMs, IAM policies, services and more from the command line.

Connecting to your new instance:
--------------------------------

We will connect to the new instance over ssh with the gcloud command:

    $ gcloud compute ssh securitymonkey --zone <ZONE>


Next:
-----

- [Back to the Quickstart](quickstart.md#install-security-monkey-on-your-instance)
