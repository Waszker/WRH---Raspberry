var tabLinks = new Array();
var contentDivs = new Array();

function init() {
    getUptime();
    getSocket();
    initCharts();

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

function getSocket() {
     var xmlHttp = new XMLHttpRequest();
     xmlHttp.onreadystatechange = function()
     {
         if(xmlHttp.readyState == 4 && xmlHttp.status == 200)
             document.getElementById("socketDiv").innerHTML = xmlHttp.responseText;
     }
     xmlHttp.open("GET", "socket", true);
     xmlHttp.send();
}

function setSocket(isTurnOn) {
     var xmlHttp = new XMLHttpRequest();
     xmlHttp.open("POST", "socket?state=" + (isTurnOn ? "on" : "off"), true);
     xmlHttp.send();
     getSocket();
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

function initCharts() {
    // dataPoints
    var dataPoints1 = [];
    var dataPoints2 = [];

    var chart = new CanvasJS.Chart("chartContainer", {
        zoomEnabled : true,
        title : {
            text : "Share Value of Two Companies"
        },
        toolTip : {
            shared : true

        },
        legend : {
            verticalAlign : "top",
            horizontalAlign : "center",
            fontSize : 14,
            fontWeight : "bold",
            fontFamily : "calibri",
            fontColor : "dimGrey"
        },
        axisX : {
            title : "chart updates every 3 secs"
        },
        axisY : {
            prefix : '$',
            includeZero : false
        },
        data : [{
            // dataSeries1
            type : "line",
            xValueType : "dateTime",
            showInLegend : true,
            name : "Company A",
            dataPoints : dataPoints1
        }, {
            // dataSeries2
            type : "line",
            xValueType : "dateTime",
            showInLegend : true,
            name : "Company B",
            dataPoints : dataPoints2
        }],
        legend : {
            cursor : "pointer",
            itemclick : function(e) {
                if ( typeof (e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
                    e.dataSeries.visible = false;
                } else {
                    e.dataSeries.visible = true;
                }
                chart.render();
            }
        }
    });

    var updateInterval = 500;
    // initial value
    var yValue1 = 640;
    var yValue2 = 604;

    var time = new Date;
    time.setHours(9);
    time.setMinutes(30);
    time.setSeconds(00);
    time.setMilliseconds(00);
    // starting at 9.30 am

    var updateChart = function(count) {
        count = count || 1;

        // count is number of times loop runs to generate random dataPoints.

        for (var i = 0; i < count; i++) {

            // add interval duration to time
            time.setTime(time.getTime() + updateInterval);

            // generating random values
            var deltaY1 = .5 + Math.random() * (-.5 - .5);
            var deltaY2 = .5 + Math.random() * (-.5 - .5);

            // adding random value and rounding it to two digits.
            yValue1 = Math.round((yValue1 + deltaY1) * 100) / 100;
            yValue2 = Math.round((yValue2 + deltaY2) * 100) / 100;

            // pushing the new values
            dataPoints1.push({
                x : time.getTime(),
                y : yValue1
            });
            dataPoints2.push({
                x : time.getTime(),
                y : yValue2
            });

        };

        // updating legend text with  updated with y Value
        chart.options.data[0].legendText = " Company A  $" + yValue1;
        chart.options.data[1].legendText = " Company B  $" + yValue2;

        chart.render();

    };

    // generates first set of dataPoints
    updateChart(3000);

    // update chart after specified interval
    setInterval(function() {
        updateChart();
    }, updateInterval);
}
