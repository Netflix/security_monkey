Postgres on GCP
===============

If you are deploying Security Monkey on GCP and decide to use Cloud SQL, it's recommended to run [Cloud SQL Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy) to connect to Postgres. To use Postgres on Cloud SQL, create a new instance from your GCP console and create a password for the `postgres` user when Cloud SQL prompts you. (If you ever need to reset the `postgres` user's password, refer to the [Cloud SQL documentation](https://cloud.google.com/sql/docs/postgres/create-manage-users).)

Enable Cloud SQL API
--------------------
To use cloud_sql_proxy you will need to enable the Google Cloud SQL API. Visit the [Cloud SQL API page](https://console.cloud.google.com/apis/api/sqladmin.googleapis.com/overview) and click 'Enable API'.

Create a service account for Cloud SQL Proxy
--------------------------------------------
To be able to run the Cloud SQL Proxy you will need to create a [Service Account](https://cloud.google.com/compute/docs/access/service-accounts) with a special role.

- Access the [Google console](https://console.cloud.google.com/home/dashboard).
- Under "IAM & Admin", select "Service accounts."
- Select "Create Service Account".
  - Name: "cloud-sql-proxy"
  - Add Role "Cloud SQL-> Cloud SQL Client"
- Select "Furnish a new private key"
  - Key type: JSON
- Click "Save"

After the instance is up, run Cloud SQL Proxy:

    $ ./cloud_sql_proxy -instances=[INSTANCE CONNECTION NAME]=tcp:5432 -credential_file=/path/to/gcp/serviceaccount/keys/key.json &

You can find the instance connection name by clicking on your Cloud SQL instance name on the [Cloud SQL dashboard](https://console.cloud.google.com/sql/instances) and looking under "Properties". The instance connection name is something like [PROJECT\_ID]:[REGION]:[INSTANCENAME].

You'll need to run Cloud SQL Proxy on whichever machine is accessing Postgres, e.g. on your local workstation as well as on the GCE instance where you're running Security Monkey.

Connect to the Postgres instance:

    $ sudo psql -h 127.0.0.1 -p 5432 -U postgres -W

After you've connected successfully in psql, follow the [Configure the DB](installation/03-install-sm.md) instructions to set up the Security Monkey database.

Next:
-----
- [Back to the Quickstart](quickstart.md#launch-an-instance)
