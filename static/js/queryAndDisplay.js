/**
 * Created by Joe on 5/4/2017.
 */
google.charts.load('current', {'packages': ['corechart']});
google.charts.setOnLoadCallback(drawChart);

function drawChart() {
    var netdata = 'https://london.my-netdata.io/api/v1/data?after=-60&format=datasource&options=nonzero&chart=';

    // define all the charts you need
    var mycharts = [
        {
            div: 'chart1_div',
            chart: 'system.cpu',
            type: 'stacked',
            options: { // these are google chart options
                title: 'System CPU',
                vAxis: {minValue: 100}
            }
        },
        {
            div: 'chart2_div',
            chart: 'system.io',
            type: 'area',
            options: { // these are google chart options
                title: 'System I/O',
            }
        },
        {
            div: 'chart3_div',
            chart: 'ipv4.tcpsock',
            type: 'line',
            options: { // these are google chart options
                title: 'TCP sockets',
            }
        }
    ];

    // initialize the google charts
    var len = mycharts.length;
    while (len--) {
        mycharts[len].query = new google.visualization.Query(netdata + mycharts[len].chart, {sendMethod: 'auto'});

        switch (mycharts[len].type) {
            case 'stacked':
                mycharts[len].options.isStacked = 'absolute';
            // no break here - render it as area chart
            case 'area':
                mycharts[len].gchart = new google.visualization.AreaChart(document.getElementById(mycharts[len].div));
                break;

            default:
                mycharts[len].gchart = new google.visualization.LineChart(document.getElementById(mycharts[len].div));
                break;
        }
    }

    function refreshChart(c) {
        c.query.send(function (data) {
            c.gchart.draw(data.getDataTable(), c.options);
        });
    }

    setInterval(function () {
        var len = mycharts.length;
        while (len--) refreshChart(mycharts[len]);
    }, 1000);
}