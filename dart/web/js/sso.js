/**
 * Created by pkelley on 6/2/16.
 */

$.urlParam = function(name){
	var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
    if (results == null) {
        return "/static/ui.html";
    }
	return results[1] || 0;
};

var create_url = function(provider) {
    var next = $.urlParam("next");
    var url = provider.authorizationEndpoint;
    url += "?response_type="+provider.responseType;
    url += "&client_id="+provider.clientId;
    url += "&redirect_uri="+provider.redirectUri;
    url += "&scope="+provider.scope.join(provider.scopeDelimiter);
    url += "&state=clientId,"+provider.clientId+",redirectUri,"+provider.redirectUri+",return_to,"+next;
    if (provider.hd) {
        url += "&hd="+provider.hd;
    }
    return url;
};

$.getJSON("/api/1/auth/providers",
    function(data) {
        console.log("Got these providers: "+JSON.stringify(data, null, 2));
        data.forEach(function(provider) {
            $("#sso_buttons").append("<button class=\"btn btn-lg btn-primary btn-block\" id=\"sso_"+provider.name+"\" name=\"submit\" type=\"submit\">"+provider.name+"</button>");
            $("#sso_"+provider.name).click(function() {
                var url = create_url(provider);
                $("#login_div").replaceWith("<h3>Proceeding to "+provider.name+"...</h3>");
                window.location.replace(url);
            });
        });
    }
);
