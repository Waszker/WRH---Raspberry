var tabLinks = new Array();
var contentDivs = new Array();

function init() {
    getUptime();
}

function getUptime() {
     var xmlHttp = new XMLHttpRequest();
     xmlHttp.onreadystatechange = function()
     {
         if(xmlHttp.readyState == 4 && xmlHttp.status == 200)
             document.getElementById("systemDiv").innerHTML = xmlHttp.responseText;
     }
     xmlHttp.open("GET", "uptime", true);
     xmlHttp.send();
}

function getRestart() {
     var xmlHttp = new XMLHttpRequest();
     xmlHttp.open("GET", "restart", true);
     xmlHttp.send();
}

/**
* Sends request to specified host on specified port and returns its response.
* Can be used when controlling some devices.
*/
function getRequest(host, port, message, callback_function) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function()
    {
        if(xmlHttp.readyState == 4 && xmlHttp.status == 200)
        callback_function(xmlHttp.responseText)
    }
    xmlHttp.open("GET", "request?host=" + host + "&port=" + port + "&message=" + message, true);
    xmlHttp.send();
}

/**
* Sends POST request to specified host on specified port and returns its response.
* Can be used when controlling some devices.
* Better than the getRequest function because POST requests don't have size limits.
*/
function postRequest(host, port, message, callbackFunction) {
    var http = new XMLHttpRequest();
    http.open("POST", "request", true);
    http.onreadystatechange = function() {
        if(http.readyState == 4 && http.status == 200 && callbackFunction != null) {
            callbackFunction(http.responseText);
        }
    }
    http.send("&host=" + host + "&port=" + port + "&message=" + message);
}

/**
* Sends request to specified host on specified port. Can be used when controlling some devices.
*/
function sendRequest(host, port, message) {
     var xmlHttp = new XMLHttpRequest();
     xmlHttp.open("POST", "request?host=" + host + "&port=" + port + "&message=" + message, true);
     xmlHttp.send();
}