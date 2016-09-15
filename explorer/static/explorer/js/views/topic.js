var minYear = 1968,
    maxYear = 2017;
$(document).ready(function() {


    var svg,
        brush,
        muteLeft,
        muteRight,
        brushg,
        brushPos = [(maxYear - minYear) - (maxYear-startYear), (maxYear - minYear) - (maxYear-endYear)],
        layers,
        years,
        m,
        n=20,
        stack = d3.layout.stack().offset("wiggle");

        var color = ["#AA9A66", "#B74934", "#221100", "#577492", "#67655D", "#332C2F", "#A81A00", "#4C3F3D", "#996622", "#117788",
                     "#AA9A66", "#B74934", "#221100", "#577492", "#67655D", "#332C2F", "#A81A00", "#4C3F3D", "#996622", "#117788",
                     "#AA9A66", "#B74934", "#221100", "#577492", "#67655D", "#332C2F", "#A81A00", "#4C3F3D", "#996622", "#117788"];
    var thisColor = color[Math.floor(Math.random() * color.length)];


    var clearRelatedTopics = function() {

    }

    var clearContainingDocuments = function () {
        $('#assignments').empty();

    }

    var addRelatedTopics = function(topics) {

    }

    var addContainingDocument = function(assignmentsElem, doc) {
        var dateRow = $('<td>' + doc.pubdate + '</td>')
        var assignmentLinkRow = $('<td><a href="/documents/' + doc.id + '/?topic='+ topic_id + '">' + doc.title + '</a></td>');
        var progressRow = $('<td><div class="progress"><div class="progress-bar" role="progressbar" aria-valuenow="'+ doc.weight +'" aria-valuemin="0" aria-valuemax="100" style="width: '+ doc.weight +'%;"><span class="sr-only">' + doc.weight.toPrecision(2)+'%</span></div></div></td>');
        var rowElem = $('<tr>');
        rowElem.append(dateRow)
            .append(assignmentLinkRow)
            .append(progressRow);

        assignmentsElem.append(rowElem);
    }

    var addContainingDocuments = function(documents) {
        documents.forEach(function(doc) {
            addContainingDocument($('#assignments'), doc);
        });
    }

    // Get documents and related topics.
    var refreshTopicData = function(start, end) {
        $.ajax('?data=json&start=' + start + '&end=' + end, {
            success: function(elements) {
                clearContainingDocuments();
                addContainingDocuments(elements.documents);
                if (end - start > 1) {
                    $('#assignmentQualifier').text(' (' + start + '\u2013' + Number(end - 1) + ')');
                } else {
                    $('#assignmentQualifier').text(' (' + start + ')');
                }
            }
        });
    }

    var draw = function() {
        var width = parseInt(d3.select('#topic-stream').style('width'), 10),
            height = parseInt(d3.select('#topic-stream').style('height'), 10);

        var x = d3.scale.linear()
            .domain([0, m - 1])
            .range([0, width]);

        var y = d3.scale.linear()
            .domain([0, d3.max(layers, function(layer) { return d3.max(layer, function(d) { return d.y0 + d.y; }); })])
            .range([height, 0]);

        var area = d3.svg.area()
            .interpolate("step-after")
            .x(function(d) { return x(d.x); })
            .y0(function(d) { return y(d.y0); })
            .y1(function(d) { return y(d.y0 + d.y); });

        var axis = d3.svg.axis()
            .scale(x)
            .orient("top")
            .tickFormat(function(d, i) {
                return String(years[d]);
            });

        svg = d3.select("#topic-stream").append("svg")
            .attr("width", width)
            .attr("height", height);

        svg.selectAll("path")
            .data(layers)
            .enter().append("path")
            .attr("d", area)
            .style("fill", thisColor);

        svg.append("g")
            .attr("class", "axis")
            .attr("transform", "translate(0," + height + ")")
            .call(axis)
                .selectAll('text')  // Rotate and reposition x axis labels.
                .attr("transform", "rotate(-90)" )
                    .attr("dx", height/2)
                    .attr("dy", "1.7em");

        brush = d3.svg.brush()
            .x(x)
            .extent(brushPos)
            .on("brushstart", brushstart)
            .on("brush", brushmove)
            .on("brushend", brushend);

        muteLeft = svg.append("rect")
            .classed('mute', true)
            .attr('fill', '#fff')
            .attr("x", 0)
            .attr("y", 0)
            .attr("width", 0)
            .attr("height", height);

        muteRight = svg.append("rect")
            .classed('mute', true)
            .attr('fill', '#fff')
            .attr("x", 0)
            .attr("y", 0)
            .attr("width", 0)
            .attr("height", height);

        var arc = d3.svg.arc()
            .outerRadius(height / 8)
            .startAngle(0)
            .endAngle(function(d, i) { return i ? -Math.PI : Math.PI; });

        brushg = svg.append("g")
                .attr("class", "brush")
                .call(brush);

        brushg.selectAll(".resize").append("path")
            .attr("transform", "translate(0," +  height / 2 + ")")
            .attr("d", arc);

        brushg.selectAll("rect")
            .attr("height", height-1);

        brushstart();
        brushmove();
        refreshTopicData(startYear, endYear);

        function brushstart() {
          svg.classed("selecting", true);
        }

        function brushmove() {
          var s = brush.extent();
          brushPos = s;

          muteLeft.attr('width', x(s[0]));
          muteRight.attr('x', x(s[1]));
          muteRight.attr('width', width - x(s[1]));
        }

        function brushend() {
            var s = brush.extent();
            s = [Math.round(s[0]), Math.round(s[1])];
            if (s[0] == s[1]) s[1] += 1;
            d3.select(this).transition()
                .call(brush.extent(s));

            muteLeft.transition()
                .attr("width", x(s[0]));
            muteRight.transition()
                .attr('x', x(s[1]))
                .attr('width', width - x(s[1]));
            startYear = 1968 + s[0];
            endYear = 1968 + s[1];

            refreshTopicData(startYear, endYear);
            svg.classed("selecting", !d3.event.target.empty());
        }
    }

    function transition() {
        d3.selectAll("path")
            .data(function() {
                var d = layers1;
                layers1 = layers0;
                return layers0 = d;
            })
            .transition()
            .duration(2500)
            .attr("d", area);
    }

    var redraw = function () {
        var width = parseInt(d3.select('#topic-stream').style('width'), 10),
            height = parseInt(d3.select('#topic-stream').style('height'), 10);

        var x = d3.scale.linear()
            .domain([0, m - 1])
            .range([0, width]);

        var y = d3.scale.linear()
            .domain([0, d3.max(layers, function(layer) { return d3.max(layer, function(d) { return d.y0 + d.y; }); })])
            .range([height, 0]);

        var area = d3.svg.area()
            .interpolate("step-after")
            .x(function(d) { return x(d.x); })
            .y0(function(d) { return y(d.y0); })
            .y1(function(d) { return y(d.y0 + d.y); });

        var axis = d3.svg.axis()
            .scale(x)
            .orient("top")
            .tickFormat(function(d, i) {
                return String(years[d]);
            });


        // Update overall dimensions.
        svg.attr("height", height)
            .attr("width", width);

        // Update stream paths.
        svg.selectAll("path")
            .data(layers)
            .attr("d", area);

        // Resize brush domain.
        function brushstart() {
          svg.classed("selecting", true);
        }

        var brushmove = function() {
          var s = brush.extent();
          brushPos = s;

          muteLeft.attr('width', x(s[0]));
          muteRight.attr('x', x(s[1]));
          muteRight.attr('width', width - x(s[1]));
        }

        var brushend = function() {
            var s = brush.extent();
            s = [Math.round(s[0]), Math.round(s[1])];
            d3.select(this).transition()
                .call(brush.extent(s));

            muteLeft.transition()
                .attr("width", x(s[0]));
            muteRight.transition()
                .attr('x', x(s[1]))
                .attr('width', width - x(s[1]));
            startYear = 1968 + s[0];
            endYear = 1968 + s[1];

            refreshTopicData(startYear, endYear);
            svg.classed("selecting", !d3.event.target.empty());
        }

        brush.x(x)
            .extent(brushPos)
            .on("brushstart", brushstart)
            .on("brush", brushmove)
            .on("brushend", brushend);

        var s = brush.extent();
        brushPos = s;

        muteLeft.attr('width', x(s[0]));
        muteRight.attr('x', x(s[1]));
        muteRight.attr('width', width - x(s[1]));

        brushg.call(brush);


        // Resize the X axis.
        d3.select('.axis')
            .attr("transform", "translate(0," + height + ")")
            .call(axis)
            .selectAll('text')  // Rotate and reposition x axis labels.
            .attr("transform", "rotate(-90)" )
                .attr("dx", height/2)
                .attr("dy", "1.7em");

    }

    var resize = function() {
        redraw();
    }

    d3.json("/topics/" + topic_id + "/?data=time", function(data) {
        n = 20; // number of layers
        m = data.values.length; // number of samples per layer

        var a = [], i;
        for (i = 0; i < m; ++i) a[i] = 0;
        var series = a.map(function(d, i) { return {x: i, y: data.values[i]}; });
        // console.log(data.values);
        layers = stack([series]);
        years = data.dates;
        draw(layers);
        d3.select(window).on('resize', resize);
    });
});
