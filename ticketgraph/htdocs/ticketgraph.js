var plot = null;
var line_tick = 86400000;
if(typeof stack_graph!=='undefined'&&stack_graph==true){
        line_tick /= 3.5;
        for(var k in closedTickets){
                closedTickets[k][0] += line_tick+5000000;
        }
        for(var k in workedTickets){
                workedTickets[k][0] += (line_tick+5000000)*2;
        }
}
$(document).ready(function() {
        var graph = $('#placeholder').width(800).height(500),
        barSettings = { show: true, barWidth: line_tick, align: 'center', stack: false};
        plot = $.plot($('#placeholder'),
        [
                {
                        data: openedTickets,
                        label: 'New tickets',
                        color: '#66cd00',
                        stack: true,
                        idx: 0
                },
                {
                        data: reopenedTickets,
                        label: 'Reopened tickets',
                        color: '#458b00',
                        stack: true,
                        idx: 1
                },
                {
                        data: closedTickets,
                        label: 'Closed tickets',
                        color: '#8b0000',
                        idx: 2
                },                {
                        data: workedTickets,
                        label: 'Worked tickets',
                        color: '#45458b',
                        idx: 3
                },
                {
                        data: openTickets,
                        label: 'Open tickets',
                        yaxis: 2,
                        lines: { show: true, steps: false },
                        bars: {show: false},
                        shadowSize: 0,
                        color: '#333',
                        idx: 4
                }
        ],
        {
                series:{
                        bars: barSettings
                },
                xaxis: { mode: 'time', minTickSize: [1, "day"] },
                grid: { hoverable: true },
                yaxis: { label: 'Tickets' },
                y2axis: { min: 0 },
                legend: {
                        container:$("#legend-container"),
                        position: 'ne',
                        labelFormatter: function(label, series){
                                return '<a href="#" onClick="tracGraphTogglePlot('+series.idx+'); return false;">'+label+'</a>';
                        }
                }
        });

        $("<div id='tooltip'></div>").css({
                        position: "absolute",
                        display: "none",
                        border: "1px solid #fdd",
                        padding: "2px",
                        "background-color": "#fee",
                        opacity: 0.80
                }).appendTo("body");


        $("#placeholder").bind("plothover", function (event, pos, item) {
                if (item) {
                        var x = item.datapoint[0],
                                y = Math.abs(item.datapoint[1]);
                        $("#tooltip").html(tracGraphTimeConverter(x) + '<br />' + item.series.label + " : " + y)
                                .css({top: item.pageY+5, left: item.pageX+5})
                                .fadeIn(200);
                } else {
                        $("#tooltip").hide();
                }
        });
//      setTimeout(function(){tracGraphTogglePlot(2);},500);
});
function tracGraphTimeConverter(timestamp){
        var a = new Date(timestamp);
        var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        var year = a.getFullYear();
        var month = months[a.getMonth()];
        var date = a.getDate();
//      var hour = a.getHours();
//      var min = a.getMinutes();
//      var sec = a.getSeconds();
        var time = month + ' ' + date + ', ' + year;
        return time;
}
function tracGraphTogglePlot(seriesIdx){
        var someData = plot.getData();
        if(typeof someData[seriesIdx].data_old === 'undefined'){
                someData[seriesIdx].data_old=someData[seriesIdx].data;
                someData[seriesIdx].data=[];
        }else{
                someData[seriesIdx].data=someData[seriesIdx].data_old;
                delete(someData[seriesIdx].data_old);
        }
        plot.setData(someData);
//      plot.setupGrid();
        plot.draw();
}
