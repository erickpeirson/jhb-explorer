var minYear = 1968,
    maxYear = 2017;

$('body').ready(function() {
    var layers,
        pieData,
        divisionData,
        years,
        m,
        n=20,
        brushPos = [(maxYear - minYear) - (maxYear-startYear), (maxYear - minYear) - (maxYear-endYear)],
        stack = d3.layout.stack().offset("wiggle");

    var color = ["#AA9A66", "#B74934", "#221100", "#577492", "#67655D", "#332C2F", "#A81A00", "#4C3F3D", "#996622", "#117788",
                 "#AA9A66", "#B74934", "#221100", "#577492", "#67655D", "#332C2F", "#A81A00", "#4C3F3D", "#996622", "#117788",
                 "#AA9A66", "#B74934", "#221100", "#577492", "#67655D", "#332C2F", "#A81A00", "#4C3F3D", "#996622", "#117788"];
    var thisColor = color[Math.floor(Math.random() * color.length)];
    var colorMap;

    var redraw = function() {
        var width = parseInt(d3.select('#topic-stream').style('width'), 10),
            height = parseInt(d3.select('#topic-stream').style('height'), 10);

        var x = d3.scale.linear()
            .domain([0, m - 1])
            .range([0, width]);

        var y = d3.scale.linear()
            .domain([0, d3.max(layers, function(layer) {
                return d3.max(layer.layer, function(d) {
                    return d.y0 + d.y;
                });
            })])
            .range([height, 0]);

        var area = d3.svg.area()
            .interpolate("cardinal")
            .x(function(d) { return x(d.x); })
            .y0(function(d) { return y(d.y0); })
            .y1(function(d) { return y(d.y0 + d.y); });

        var axis = d3.svg.axis()
            .scale(x)
            .orient("top")
            .tickFormat(function(d, i) {
                return String(years[d]);
            });

        var svg = d3.select("#topic-stream").append("svg")
            .attr("width", width)
            .attr("height", height);

        svg.selectAll("path")
            .data(layers)
            .enter().append("path")
            .attr("d", function(d) {
                return area(d.layer);
            })
            .style("fill", function(d) {
                return color[d.t];
            })
            .classed('stream', true)
            .attr("id", function(d) {
                // So that we can highlight the stream when the user clicks a node.
                return 'topic-stream-area-' + String(d.t);
            });

        svg.append("g")
            .attr("class", "axis")
            .attr("transform", "translate(0," + height + ")")
            .call(axis)
                .selectAll('text')  // Rotate and reposition x axis labels.
                .attr("transform", "rotate(-90)" )
                    .attr("dx", height/2)
                    .attr("dy", "1.7em");


        var brush = d3.svg.brush()
            .x(x)
            .extent(brushPos)
            .on("brushstart", brushstart)
            .on("brush", brushmove)
            .on("brushend", brushend);

        var muteLeft = svg.append("rect")
            .classed('mute', true)
            .attr('fill', '#fff')
            .attr("x", 0)
            .attr("y", 0)
            .attr("width", 0)
            .attr("height", height);

        var muteRight = svg.append("rect")
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

        var brushg = svg.append("g")
                .attr("class", "brush")
                .call(brush);

        brushg.selectAll(".resize").append("path")
            .attr("transform", "translate(0," +  height / 2 + ")")
            .attr("d", arc);

        brushg.selectAll("rect")
            .attr("height", height-1);

        brushstart();
        brushmove();

        function brushstart() {
          svg.classed("selecting", true);
        }

        function brushmove() {
            var s = brush.extent();
            brushPos = s;
            muteLeft.attr('width', x(s[0]));
            muteRight.attr('x', x(s[1]));
            muteRight.attr('width', width - x(s[1]));

            s = [Math.round(s[0]), Math.round(s[1])];
            startYear = minYear + s[0];
            endYear = minYear + s[1];
            recalculatePieData();
        }

        function brushend() {
            var s = brush.extent();
            s = [Math.round(s[0]), Math.round(s[1])];
            if (s[0] == s[1]) s[1] += 1;
            d3.select(this).transition()
                .call(brush.extent(s));
            brushmove();
            transitionPie();

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

    function resize() {
        console.log('resize!');
        $("#topic-stream").empty();

        redraw();
        redrawPie();
        d3.select('#organism-list').style('max-height', getOrgListHeight());
    }

    var recalculatePieData = function() {
        pieData = [];
        // console.log(divisionData);
        divisionData.divisions.forEach(function(division, i) {
            useValues = [];
            division.dates.forEach(function(date, i) {
                if ((startYear <= date) &  (date <= endYear)) {
                    useValues.push(division.values[i]);
                }
            });
            pieData.push({
                'division': division.division,
                'sum': useValues.reduce(function(a, b) {
                    return a + b;
                }),
                'idx': i,
            });
        });
        return pieData;
    }

    var pieWidth,
        pieHeight,
        radius;
    var pieText, selectedDivision, selectedDivisionText;

    var arc = d3.svg.arc()
        .outerRadius(radius - 10)
        .innerRadius(radius - (radius/2));

    var labelArc = d3.svg.arc()
        .outerRadius(radius - 40)
        .innerRadius(radius - (radius/2));

    var pie = d3.layout.pie()
        .sort(null)
        .value(function(d) { return d.sum; });

    /**
      * Shift data values based on time period selection.
      */
    var transitionPie = function() {
        recalculatePieData();
        var path = d3.select("#pie>svg").selectAll("path");
        path.data(pie(pieData));
        path.transition().duration(750).attrTween("d", function(a) {
            var i = d3.interpolate(this._current, a);
            this._current = i(0);
            return function(t) {
                return arc(i(t));
            };
        });

        loadOrganisms();
    }

    /**
      * Completely re-draw the pie chart, e.g. when the window is resized.
      */
    var redrawPie = function() {
        $("#pie").empty();

        pieWidth = parseInt(d3.select('#pie').style('width'), 10);
        pieHeight = parseInt(d3.select('#pie').style('width'), 10);
        radius = Math.min(pieWidth, pieHeight) / 2;
        d3.select('#organism-list').style('max-height', getOrgListHeight);

        arc = d3.svg.arc()
            .outerRadius(radius - 10)
            .innerRadius(radius - (radius/2));

        labelArc = d3.svg.arc()
            .outerRadius(radius - 40)
            .innerRadius(radius - (radius/2));

        pie = d3.layout.pie()
            .sort(null)
            .value(function(d) { return d.sum; });

        var svg = d3.select("#pie").append("svg")
            .attr("width", pieWidth)
            .attr("height", pieHeight)
            .append("g")
            .attr("transform", "translate(" + pieWidth / 2 + "," + pieHeight / 2 + ")");

        pieText = svg.append('text')
            .attr("text-anchor", "middle")
            .style("visibility", function() { if (selectedDivision > 0) return "visible"; return "hidden"; })
            .text(selectedDivisionText);

        recalculatePieData();

        var g = svg.selectAll("path")    // The pie wedges.
            .data(pie(pieData))
            .enter()
            .append("path")
            .attr("class", "arc")
            .attr("fill", function(d) { return color[d.data.idx]; })
            .attr("d", arc)
            .each(function(d) {
                this._current = d;
            })

        // Maintain selection styling.
        g.style("opacity", function(d) {
            if (selectedDivision === undefined) return 1.0;
            if (selectedDivision == d.data.idx) return 1.0;
            return 0.5;
        });
        d3.selectAll('.stream').style('opacity', function(d) {
            if (selectedDivision === undefined) return 1.0;
            if (selectedDivision == d.t) return 1.0;
            return 0.1;
        });

        g.append("svg:title")
            .text(function(d) { return d.data.division; });

        // User hovers over a wedge of the pie.
        g.on("mouseover", function() {
            var elem = this;

            // Show division label.
            pieText.text(function(d) { return elem._current.data.division; })
                .style("visibility", "visible");

            // Highlight the hovered wedge.
            g.style('opacity', function(d) { if (d.data.idx != selectedDivision) return 0.5; return 1.0; });
            d3.select(this).style('opacity', 1.0);
            // Highlight the corresponding time-series stream.
            d3.selectAll('.stream').style('opacity', function(d) {
                if (selectedDivision === undefined) return 0.1;
                if (selectedDivision == d.t) return 1.0; return 0.1;
            });
            d3.select('#topic-stream-area-' + String(this._current.data.idx)).style('opacity', 1.0);

        });

        // User moves mouse away from pie chart.
        g.on("mouseout", function() {
            g.style("opacity", function(d) {
                if (selectedDivision === undefined) return 1.0;
                if (selectedDivision == d.data.idx) return 1.0; return 0.5;
            });

            d3.selectAll('.stream').style('opacity', function(d) {
                if (selectedDivision === undefined) return 1.0;
                if (selectedDivision == d.t) return 1.0; return 0.1;
            });

            pieText.text(function(d) { if (selectedDivision > 0) return selectedDivisionText; return; });
        });

        // User clicks on a wedge of the pie chart.
        g.on("click", function() {
            // We use these to persist highlighting and labels, and to select
            //  which organisms are shown in the table.
            selectedDivision = this._current.data.idx;
            selectedDivisionText = this._current.data.division;

            // Highlight the corresponding stream.
            d3.selectAll('.stream').style('opacity', function(d) {
                if (selectedDivision === undefined) return 1.0;
                if (selectedDivision == d.t) return 1.0; return 0.1;
            });
            loadOrganisms();
        });

    }


    d3.json("/organisms/?data=time", function(data) {
        divisionData = data;
        n = data.divisions.length
        m = data.divisions[0].values.length; // number of samples per layer

        colorMap = {};
        data.divisions.forEach(function(division, i) {
            colorMap[division.division] = color[i];
        });

        var dataLayer = function(dt) {
            var a = [], i;
            for (i = 0; i < m; ++i) a[i] = 0;

            var series = a.map(function(d, i) {
                return {
                    x: i,
                    y0: 0,
                    y: data.divisions[dt].values[i]
                };
            });
            return series;
        }
        layers = stack(d3.range(data.divisions.length).map(function(dt) {
            return dataLayer(dt);
        })).map(function(l, i) {
            return {t: i, layer:l };
        });

        years = data.divisions[0].dates;
        redraw(layers);
        redrawPie();
        loadOrganisms();

        d3.select(window).on('resize', resize);
    });

    var organismList = $('#organism-list');

    var getOrgListHeight = function() {
        return pieHeight - 100;
    }
    var loadOrganisms = function() {
        var orgFormat = function(organism) {
            orgString = '';
            if (['species', 'genus', 'subgenus', null].indexOf(organism.rank) > -1 ) {
                orgString += '<em>' + organism.scientific_name + '</em>';
            } else {
                orgString += organism.scientific_name;
            }
            if (organism.rank != null) {
                 orgString += ' <span class="label label-default">' + organism.rank + '</span>';
            }
            return orgString;
        }

        var orgHeadingFormat = function(data) {
            headingString = 'Top ' + data.length;
            if (selectedDivisionText) {
                headingString += ' ' + selectedDivisionText.toLowerCase();
            } else {
                headingString += ' organisms';
            }
            endYear -= 1;
            headingString += ' (' + startYear + '\u2013' + endYear + ')';
            return headingString;

        }
        organismList.empty();

        d3.json("/organisms/?data=json&start=" + startYear + "&end=" + endYear + '&division=' + selectedDivisionText, function(data) {
            data.data.forEach(function(organism) {
                organismList.append('<a href="/organisms/' + organism.id+ '/" class="list-group-item">'+ orgFormat(organism) +' <span class="label label-danger pull-right">' + organism.occurrences + '</span></a>')
            });
            d3.select('#organism-list-heading').text(orgHeadingFormat(data.data));

        });
    };
    // loadOrganisms();
});
