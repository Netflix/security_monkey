Setup Nginx:
------------

Security Monkey uses gunicorn to serve up content on its internal 127.0.0.1 address. For better performance, and to offload the work of serving static files, we wrap gunicorn with nginx. Nginx listens on 0.0.0.0 and proxies some connections to gunicorn for processing and serves up static files quickly.

### securitymonkey.conf

Copy the config file into place:

    sudo cp /usr/local/src/security_monkey/nginx/security_monkey.conf /etc/nginx/sites-available/security_monkey.conf
    sudo ln -s /etc/nginx/sites-available/security_monkey.conf /etc/nginx/sites-enabled/security_monkey.conf
    sudo rm /etc/nginx/sites-enabled/default
    sudo service nginx restart
    
### Start the API server

Manually start Security Monkey with `monkey run_api_server`. Setting up autostart is explained later in this documentation.

--
### Next step: [Login to Security Monkey & load data](07-load-data.md)
--
