What does the Security Monkey architecture look like?
---------------
Security Monkey operates in a hub-spoke type of model where Security Monkey lives in one account,
but then "reaches into" other accounts to describe and collect details.

More details on this are outlined in the IAM section for each respective infrastructure.

The components that make up Security Monkey are as follows (not AWS specific):
![diagram](images/sm_instance_diagram.png)

All of the components in the diagram should reside within the same account and region.

IAM Permissions Access Diagram
------------
Security Monkey accesses accounts to scan via credentials it is provided ("Role Assumption" where available).
![diagram](images/sm_iam_diagram.png)
