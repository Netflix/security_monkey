IAM Role Setup on GCP
=====================

Below describes how to install Security Monkey on GCP.

Install gcloud
---------------

If you haven't already, install *gcloud* from the [downloads](https://cloud.google.com/sdk/downloads) page.  *gcloud* enables you to administer VMs, IAM policies, services and more from the command line.

Setup Service Account
---------------------

To restrict which permissions Security Monkey has to your projects, we'll create a [Service Account](https://cloud.google.com/compute/docs/access/service-accounts) with a special role.

- Access the [Google console](https://console.cloud.google.com/home/dashboard).
- Under "IAM & Admin", select "Service accounts."
- Select "Create Service Account".
  - Name: "securitymonkey"
  - Add Role "IAM->SecurityReviewer"
  - Add Role "Project->Viewer"
  - If you're going to monitor your GCP services from an AWS instance, check the box "Furnish a new private key" and ensure JSON is selected as the Key type.
  - Hit "Create"

![Create Service Account](images/create_service_account.png "Create Service Account")

 - Select the newly created "securitymonkey" services account and click on "Permissions".
   -  Type in your Google email adddress and select the Owner role.
   -  Press "Add".

![Add User to Service Account](images/add_user_to_service_account.png "Add User to Service Account")


Next:
-----

- [Back to the Quickstart](quickstart.md#database)