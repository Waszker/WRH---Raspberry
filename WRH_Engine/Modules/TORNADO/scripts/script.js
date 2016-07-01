var tabLinks = new Array();
var contentDivs = new Array();

function init() {
    getUptime();

    // Grab the tab links and content divs from the page
    var tabListItems = document.getElementById('tabs').childNodes;
    for (var i = 0; i < tabListItems.length; i++) {
        if (tabListItems[i].nodeName == "LI") {
            var tabLink = getFirstChildWithTagName(tabListItems[i], 'A');
            var id = getHash(tabLink.getAttribute('href'));
            tabLinks[id] = tabLink;
            contentDivs[id] = document.getElementById(id);
        }
    }

    // Assign onclick events to the tab links, and
    // highlight the first tab
    var i = 0;

    for (var id in tabLinks ) {
        tabLinks[id].onclick = showTab;
        tabLinks[id].onfocus = function() {
            this.blur();
        };
        if (i == 0)
            tabLinks[id].className = 'selected';
        i++;
    }

    // Hide all content divs except the first
    var i = 0;

    for (var id in contentDivs ) {
        if (i != 0)
            contentDivs[id].className = 'tabContent hide';
        i++;
    }
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
* Sends request to specified host on specified port. Can be used when controlling some devices.
*/
function sendRequest(host, port, message) {
     var xmlHttp = new XMLHttpRequest();
     xmlHttp.open("POST", "request?host=" + host + "&port=" + port + "&message=" + message, true);
     xmlHttp.send();
}


function showTab() {
    var selectedId = getHash(this.getAttribute('href'));

    // Highlight the selected tab, and dim all others.
    // Also show the selected content div, and hide all others.
    for (var id in contentDivs ) {
        if (id == selectedId) {
            tabLinks[id].className = 'selected';
            contentDivs[id].className = 'tabContent';
        } else {
            tabLinks[id].className = '';
            contentDivs[id].className = 'tabContent hide';
        }
    }

    // Stop the browser following the link
    return false;
}

function getFirstChildWithTagName(element, tagName) {
    for (var i = 0; i < element.childNodes.length; i++) {
        if (element.childNodes[i].nodeName == tagName)
            return element.childNodes[i];
    }
}

function getHash(url) {
    var hashPos = url.lastIndexOf('#');
    return url.substring(hashPos + 1);
}