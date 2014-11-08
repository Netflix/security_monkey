library security_monkey.constants;

/**
 ** REMOTE_AUTH:
 **  FALSE - When the API 403's, just redirect to /login.
 **   Nginx should proxy the request through to the python login page.
 **  TRUE - When the API 403's, redirect the browser to whatever URL is provided by the API.
 **   This is useful for third party authentication like SAML.
 **/

// LOCAL DEV
//final String API_HOST = 'http://127.0.0.1:5000/api/1';
//final bool REMOTE_AUTH = true;

// Same Box
final String API_HOST = '/api/1';
final bool REMOTE_AUTH = false;

// Also update a few places in /web/js/searchpage.js

