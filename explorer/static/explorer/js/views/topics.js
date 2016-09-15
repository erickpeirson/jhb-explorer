
var opts = {
  lines: 13 // The number of lines to draw
, length: 21 // The length of each line
, width: 14 // The line thickness
, radius: 42 // The radius of the inner circle
, scale: 1 // Scales overall size of the spinner
, corners: 1 // Corner roundness (0..1)
, color: '#577492' // #rgb or #rrggbb or array of colors
, opacity: 0.25 // Opacity of the lines
, rotate: 0 // The rotation offset
, direction: 1 // 1: clockwise, -1: counterclockwise
, speed: 1 // Rounds per second
, trail: 62 // Afterglow percentage
, fps: 20 // Frames per second when using setTimeout() as a fallback for CSS
, zIndex: 2e9 // The z-index (defaults to 2000000000)
, className: 'spinner' // The CSS class to assign to the spinner
, top: '40%' // Top position relative to parent
, left: '50%' // Left position relative to parent
, shadow: false // Whether to render a shadow
, hwaccel: false // Whether to use hardware acceleration
, position: 'absolute' // Element positioning
}


var minYear = 1968,
    maxYear = 2017;

var selectedTopic = [];
var cy;
var svg,
    brush,
    muteLeft,
    muteRight,
    brushg;
var topicWeights = {};

/**
  * When the user clicks on a node, or somehow otherwise selects a topic, we
  *  scale the height of the stream so that it is easier to see trends over
  *  time.
  */
var magnifyStream = function(streamData) {
    // We want to use up the whole available height; the max value for this
    //  topic should scale to the max height.
    var maxHeight = Math.max.apply(Math, streamData[0].layer.map(function(o){ return o.y; }));
    return [{
        t: streamData[0].t,
        maxHeight: maxHeight,       // We need this to scale down later.
        layer: streamData[0].layer.map(function(pos) {
            return {
                x: pos.x,
                y: 4500 * pos.y / maxHeight,
                y0: pos.y0 / 3.     // Drops the baseline down to make room.
            };
        })
    }];
}


/**
  * When a focal topic is deselected, we reverse the scaling performed in
  *  magnifyStream() (above).
  */
var unMagnifyStream = function(streamData) {
    return [{
        t: streamData[0].t,
        layer: streamData[0].layer.map(function(pos) {
            return {
                x: pos.x,
                y: (pos.y / 5000.) * streamData[0].maxHeight,
                y0: pos.y0 * 3.
            };
        })
    }];
}

var selectNode = function(node, duration) {
    node.select();

    var directlyConnected = node.neighborhood();
    var nonConnected = cy.elements().difference( directlyConnected );

    directlyConnected.nodes().addClass('connectedNodes');
    nonConnected.nodes().addClass('nonConnectedNodes');
    node.removeClass('nonConnectedNodes');
    node.neighborhood('edge').edges().addClass('connectedEdge');

    // Center and fit the selected node and its direct neighbors.
    var centerOn = directlyConnected.add(node);
    cy.animate({fit: {eles: centerOn, padding: 100}}, {duration: duration});

}

var triggerListView = function(e) {
    // Swap buttons.
    $('#listViewButton').css('display', 'none');
    $('#graphViewButton').css('display', 'block');

    // Show list view.
    $('#topicListContainer').css('display', 'block');
    $('#networkVisContainer').height(0);
    $('#networkVisContainer').css('height', 0);
    $('#networkVisContainer').css('visibility', 'hidden');

    $('.topic-list-item').removeClass('selected');
    $('#topic-list-item-' + selectedTopic[0]).addClass('selected');
    $('#topicListContainer').scrollTop($('#topicListContainer').scrollTop() + $('#topic-list-item-' + selectedTopic[0]).position().top-50);

}

var triggerGraphView = function(e) {

    $('#graphViewButton').css('display', 'none');
    $('#listViewButton').css('display', 'block');

    // Show graph view.
    $('#networkVisContainer').height(600);
    $('#networkVisContainer').css('height', 600);
    $('#topicListContainer').css('display', 'none');
    $('#networkVisContainer').css('visibility', 'visible');

}


var topicData = {},
    activateTopic,
    topicProminence = {};
var top10;

// When the page is loaded, request the topic colocation network.
$(document).ready(function() {
    $.ajax('?data=json', {
        success: function(data) {
            data.forEach(function(elem) {
                topicProminence[elem.id] = elem.prominence;
            });
        }
    });



    $('#listViewButton').click(triggerListView);
    $('#graphViewButton').click(triggerGraphView);

    var adjustGraphHeight = function(e) {
        var graphWidth = $('#cyTopics').width();
        if (graphWidth < 400) {
            $('#cyTopics').height(graphWidth);
        }
    }
    $(window).on('resize', adjustGraphHeight);
    $(window).ready(adjustGraphHeight);


    var buildGraph = function(startYear, endYear) {
        // While awaiting the graph data, a spinner is shown in the
        //  network visualization panel.
        $('#networkVisContainer').spin(opts);
        $('#topicListContainer').spin(opts);
        $.ajax('?data=graph&startyear=' + startYear + '&endyear=' + endYear, {
            success: function(elements) {

                // Stop the spinner.
                $('#networkVisContainer').spin(false);

                // When the data is returned, generate an interative visualization
                //  using Cytoscape.js.
                var minEdgeWeight = 1.0;
                var maxEdgeWeight = 0.0;
                var minNodeWeight = 1.0;
                var maxNodeWeight = 0.0;


                $('#listViewList').empty();
                var getWeight = function(tid) {
                    var _w = topicWeights[Number(tid)].reduce(function(i, e) {
                        if ((Number(startYear) <= Number(e.date)) && (Number(e.date) < Number(endYear))) {
                            return i + e.value;
                        } else {
                            return i;
                        }
                    }, 0);
                    var _s = topicWeights[Number(tid)].reduce(function(i, e) { return i + e.value; }, 0);
                    // console.log(_w, _s);
                    return _w/_s;
                }
                var maxWeight = Math.max.apply(Math, elements.map(function(o) {
                    if (o.data.label) {
                        return getWeight(o.data.id);
                    }  else {
                        return 0.
                    }
                }));

                function sort_by_weight(a, b) {
                    if (a.data.label && b.data.label) {  // Node.
                        var w_a = getWeight(a.data.id);///topicProminence[Number(a.data.id)];
                        var w_b = getWeight(b.data.id);///topicProminence[Number(b.data.id)];
                        return ((w_a > w_b) ? -1 : (w_a < w_b) ? 1 : 0);
                    } else {    // Edge.
                        return 1;
                    }
                }

                elements.sort(sort_by_weight);
                top10 = [];
                elements.forEach(function(elem) {
                    // We only want nodes; nodes are the only elements with
                    //  labels.

                    if (elem.data.label) {
                        if (top10.length < 20) top10.push(elem.data.id);
                        topicData[elem.data.id] = elem.data;
                        // console.log(topicProminence[elem.data.id]);
                        var w = 100*getWeight(elem.data.id)/maxWeight;///topicProminence[Number(elem.data.id)];

                        // Build the list view.
                        var progress_elem = '<div class="col-xs-2"><div class="progress"><div class="progress-bar" role="progressbar" aria-valuenow="' + w + '" aria-valuemin="0" aria-valuemax="100" style="width: ' + w + '%;"><span class="sr-only">' + w + '%</span></div></div></div>';
                        var topic_list_elem = '<a href="javascript:activateTopic('+elem.data.id+')" class="list-group-item topic-list-item" id="topic-list-item-'+elem.data.id+'"><div class="row"><div class="col-xs-10">' + elem.data.label + '</div> '+progress_elem+'</div></a>';

                        $('#listViewList').append(topic_list_elem);

                    }

                    // Normalize weights for graph.
                    var weight = Number(elem.data.weight);
                    if (elem.data.source) {  // Edge.
                        if (weight > maxEdgeWeight) maxEdgeWeight = weight;
                        if (weight < minEdgeWeight) minEdgeWeight = weight;
                    } else {
                        if (weight > maxNodeWeight) maxNodeWeight = weight;
                        if (weight < minNodeWeight) minNodeWeight = weight;
                    }
                });

                $('#topicListContainer').spin(false);

                minNodeWeight = Number(minNodeWeight.toPrecision(4));
                maxNodeWeight = Number(maxNodeWeight.toPrecision(4));
                minEdgeWeight = Number(minEdgeWeight.toPrecision(4));
                maxEdgeWeight = Number(maxEdgeWeight.toPrecision(4));

                cy = cytoscape({
                    container: $('#cyTopics'),
                    elements: elements,
                    minZoom: 0.1,
                    maxZoom: 3,
                    panningEnabled: true,
                    style: [    // The stylesheet for the graph.
                        {
                            // Node size is a function of topic prevalence.
                            selector: 'node',
                            style: {
                                'background-color': '#B74934',
                                'border-color': '#AA9A66',
                                'border-width': 2,
                                'label': 'data(label)',
                                'width': 'mapData(weight, ' + minNodeWeight  + ', ' + maxNodeWeight + ', 25, 100)',
                                'height': 'mapData(weight, ' + minNodeWeight  + ', ' + maxNodeWeight + ', 25, 100)',
                                'font-size': 'mapData(weight, ' + minNodeWeight + ', ' + maxNodeWeight + ', 24, 52)'
                            }
                        },
                        {
                            selector: 'node.connectedNodes',
                            style: {
                                'opacity': 1.0,
                                'border-color': '#AA9A66',
                                'border-width': 4,
                                'width': 'mapData(weight, ' + minNodeWeight  + ', ' + maxNodeWeight + ', 35, 85)',
                                'height': 'mapData(weight, ' + minNodeWeight  + ', ' + maxNodeWeight + ', 35, 85)',
                                'font-size': 'mapData(weight, ' + minNodeWeight + ', ' + maxNodeWeight + ', 24, 52)'
                            }
                        },
                        {
                            selector: 'node.nonConnectedNodes',
                            style: {
                                'opacity': 0.5,
                            }
                        },
                        {
                            // When a node is selected, it should be larger
                            //  and have a colored border.
                            selector: 'node:selected',
                            style: {
                                'opacity': 1.0,
                                'border-color': '#A76E07',
                                'border-width': 10,
                                'font-size': 'mapData(weight, ' + minNodeWeight + ', ' + maxNodeWeight + ', 35, 75)',
                                'width': 'mapData(weight, ' + minNodeWeight  + ', ' + maxNodeWeight + ', 80, 160)',
                                'height': 'mapData(weight, ' + minNodeWeight  + ', ' + maxNodeWeight + ', 80, 160)',
                            }
                        },
                        {
                            // Active nodes should be slightly larger.
                            selector: 'node:active',
                            style: {
                                'width': 'mapData(weight, ' + minNodeWeight  + ', ' + maxNodeWeight + ', 30, 60)',
                                'height': 'mapData(weight, ' + minNodeWeight  + ', ' + maxNodeWeight + ', 30, 60)',
                            }
                        },
                        {
                            // Edge weight is a function of nPMI.
                            selector: 'edge',
                            style: {
                                'width': 'mapData(weight, ' + minEdgeWeight  + ', ' + maxEdgeWeight + ', 1, 12)',
                                'opacity': 'mapData(weight, 0.01, 0.5, 0.1, 1)',
                                'line-color': '#67655D',
                                'target-arrow-color': '#ccc',
                            },
                        },
                        {
                            selector: 'edge.connectedEdge',
                            style: {
                                'opacity': 1,
                                'line-color': '#A76E07',
                                'z-index': 500,
                                'width': 'mapData(weight, ' + minEdgeWeight  + ', ' + maxEdgeWeight + ', 4, 36)',
                            }
                        },
                        {
                            // A selected edge should be slightly thicker, and be colored a brighter color.
                            selector: 'edge:selected',
                            style: {
                                'width': 'mapData(weight, ' + minEdgeWeight  + ', ' + maxEdgeWeight + ', 2, 8)',
                                'opacity': 1,
                                'line-color': '#AA9A66',
                            }
                        },
                    ],

                    // Pre-calculated joint force layout.
                    layout: {
                        name: 'preset',
                        positions: function(d) {
                            pos = d._private.data.pos;
                            // Scale. TODO: should we just change the boundingBox?
                            return {x: (pos.x + 0.5) * 1800, y:(pos.y + 0.5) * 1800};
                        },
                        boundingBox:  { x1: 0, y1: 0, w: 900, h: 900},
                    }
                });

                var displayTopicDetails = function(topic_id) {
                    var nodeData = topicData[topic_id];

                    // var nodeData = node.data();
                    $('.topic-details').css('visibility', 'visible');

                    /**
                      *  Ensure (relatively) consistent display of terms by
                      *  normalizing the topic-term posterior by the max
                      *  posterior value for this topic.
                      */
                    var normalize_weight = function(weight, max_weight) {
                        return Math.max(1.5, 3*weight/max_weight);
                    }

                    // Load and display the top 20 terms for this topic.
                    $.get('/topics/' + nodeData.id + '/?data=terms', {}, function(data) {
                            $('#topic-details-documents-heading-label').text(data.label);
                            $('#topic-details-documents-heading-qualifier').text(startYear +'\u2013'+ endYear);
                            $('#topic-details-heading-1')
                                .text('View details about this topic');

                            // `vw` is "viewport width" -- responsive font size!
                            data.terms.forEach(function(term) {
                                $('#topic-details-terms-1-list')
                                    .append('<li class="topic-details-term" style="font-size: '+ normalize_weight(term.weight, data.terms[0].weight) +'vw;">' + term.term + '</li>');
                            });
                            $('#topic-details-1-link').attr('href', '/topics/' + nodeData.id + '/');
                            $('#topic-details-1-link').css('visibility', 'visible');
                    });

                    $.get('/topics/' + nodeData.id + '/?data=documents&start=' + startYear + '&end=' + endYear, {}, function(data) {
                        data.documents.forEach(function(doc) {
                            $('#topic-details-documents')
                                .append('<tr class="h6">' +
                                    '<td>' + doc.pubdate + '</td>' +
                                    '<td><a class="" href="/documents/'+ doc.id +'/?topic='+ nodeData.id +'">'+ doc.title +'</a></td>'+
                                    '<td><div class="progress"><div class="progress-bar" role="progressbar" aria-valuenow="' + doc.weight + '" aria-valuemin="0" aria-valuemax="100" style="width: ' + doc.weight + '%;"><span class="sr-only">' + doc.weight + '%</span></div></div></td>' +
                                    '</tr>');
                        });
                    });
                }


                var clearTopicDetails = function() {
                    $('.topic-details').css('visibility', 'hidden');
                    $('#topic-details-terms-2-list').empty();
                    $('#topic-details-heading-2').empty();
                    $('.topic-details-2').css('visibility', 'hidden');


                    $('#topic-details-terms-1-list').empty();
                    $('#topic-details-heading-1').empty();
                    $('#topic-details-1-link').css('visibility', 'hidden');
                    $('.topic-details-1').css('visibility', 'hidden');

                    $('#topic-details-documents').empty();

                    $('#topic-details-documents-heading-label').empty();
                    $('#topic-details-documents-heading-qualifier').empty();
                }

                var clearSelectedTopics = function() {
                    clearTopicDetails();

                    cy.elements('edge').edges().removeClass('connectedEdge');
                    cy.elements('edge').edges().removeClass('nonConnected');
                    cy.elements('edge').edges().unselect();
                    cy.elements('node').nodes().removeClass('connectedNodes');
                    cy.elements('node').nodes().removeClass('nonConnectedNodes');
                    cy.elements('node').nodes().unselect();

                    clearSelectedStreams();
                }

                var clearSelectedStreams = function() {
                    d3.selectAll('.stream')
                        .classed('stream-muted', false);
                    d3.selectAll('.stream-highlighted')
                        .classed('stream-highlighted', false);

                    selectedTopic.forEach(function(topic) {
                        var streamElem = d3.select('#topic-stream-area-' + topic);
                        redrawStream(streamElem, unMagnifyStream(streamElem.data()));
                    });
                    selectedTopic = [];

                    d3.selectAll('.stream').style('opacity', 1.0);
                }

                activateTopic = function(topic_id) {
                    clearSelectedTopics();
                    clearTopicDetails();
                    selectedTopic.push(topic_id);
                    displayTopicDetails(topic_id);
                    d3.selectAll('.stream').style('opacity', 0.1);

                    $('.topic-list-item').removeClass('selected');
                    $('#topic-list-item-' + topic_id).addClass('selected');
                    $('#topicListContainer').scrollTop($('#topicListContainer').scrollTop() + $('#topic-list-item-' + topic_id).position().top-50);

                    var streamElem = d3.select('#topic-stream-area-' + topic_id);
                    streamElem.style('opacity', 1.0);
                    redrawStream(streamElem, magnifyStream(streamElem.data()));

                    selectNode(cy.$('#' + topic_id), 750);
                }

                var handleNodeTap = function(event, activate) {
                    var node = event.cyTarget;  // The node that was clicked.
                    var topic_id = node._private.data.id;

                    activateTopic(topic_id);
                    // selectNode(node, 750);
                }

                // When a node is clicked, information about the corresponding
                //  topic is displayed in a neighboring panel.
                cy.on('tap', 'node', handleNodeTap);
                cy.edges().unselectify();



                // When the esc key is pressed, clear all selections.
                $(document).keyup(function(e) {
                     if (e.keyCode == 27) {
                        clearSelectedTopics();
                        $('#id_q').val('').attr('pk', '');
                    }
                });

                clearTopicDetails();

                // A topic is pre-selected, usually because the user selected
                //  one in a previous state of the graph.
                if (selectedTopic.length > 0) {
                    // Reselect node.
                    // TODO: this probably doesn't need to be an array.
                    selectedTopic.forEach(function(topic) {
                        selectNode(cy.$('#' + topic), 0);
                    });
                    displayTopicDetails(selectedTopic[0]);  //cy.$('#' + selectedTopic[0])
                    $('.topic-list-item').removeClass('selected');
                    $('#topic-list-item-' + selectedTopic[0]).addClass('selected');
                    $('#topicListContainer').scrollTop($('#topicListContainer').scrollTop() + $('#topic-list-item-' + selectedTopic[0]).position().top-50);
                // If no node is pre-selected, choose a node at random.
                } else {    // TODO: Number of topics shouldn't be hardcoded.


                    var randomNode = cy.$('#' + top10[Math.floor((Math.random() * 10))]);
                    // Mimic user selection of the topic.
                    randomNode.trigger('tap');

                }
            }
        });
    }

    var layers,
        years,
        m,
        n = 20,
        brushPos = [49 - (maxYear-startYear), 49 - (maxYear-endYear)],
        stack = d3.layout.stack().offset("wiggle");

        var color = ["#AA9A66", "#B74934", "#221100", "#577492", "#67655D", "#332C2F", "#A81A00", "#4C3F3D", "#996622", "#117788",
                     "#AA9A66", "#B74934", "#221100", "#577492", "#67655D", "#332C2F", "#A81A00", "#4C3F3D", "#996622", "#117788",
                     "#AA9A66", "#B74934", "#221100", "#577492", "#67655D", "#332C2F", "#A81A00", "#4C3F3D", "#996622", "#117788"];
    var thisColor = color[Math.floor(Math.random() * color.length)];

    /**
      * Update a single stream with new data.
      */
    var redrawStream = function(streamElem, streamData) {
        var width = parseInt(d3.select('#topic-stream').style('width'), 10),
            height = parseInt(d3.select('#topic-stream').style('height'), 10);

        var x = d3.scale.linear()
            .domain([0, m - 1])
            .range([0, width]);

        var y = d3.scale.linear()
            .domain([0, d3.max(layers, function(layer) {return d3.max(layer.layer, function(d) { return d.y0 + d.y; }); })])
            .range([height, 0]);

        var area = d3.svg.area()
            .interpolate("step-after")
            .x(function(d) { return x(d.x); })
            .y0(function(d) { return y(d.y0); })
            .y1(function(d) { return y(d.y0 + d.y); });

        streamElem.data(streamData)
            .transition()
            .duration(750)
            .attr("d", function(d) {
                return area(d.layer);
            });
    }

    var redraw = function () {
        var width = parseInt(d3.select('#topic-stream').style('width'), 10),
            height = parseInt(d3.select('#topic-stream').style('height'), 10);

        var x = d3.scale.linear()
            .domain([0, m - 1])
            .range([0, width]);

        var y = d3.scale.linear()
            .domain([0, d3.max(layers, function(layer) {return d3.max(layer.layer, function(d) { return d.y0 + d.y; }); })])
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
            .attr("d", function(d) {
                return area(d.layer);
            });

        // Renew magnification of selected stream(s).
        selectedTopic.forEach(function(topic) {
            var selectedElem = d3.select('#topic-stream-area-' + topic);
            selectedElem.data(magnifyStream(selectedElem.data()))
                .attr("d", function(d) {
                    return area(d.layer);
                });
        });

        // Resize brush domain.
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
            // brush.extent(s);
            d3.select(this).transition()
                .call(brush.extent(s));

            muteLeft.transition()
                .attr("width", x(s[0]));
            muteRight.transition()
                .attr('x', x(s[1]))
                .attr('width', width - x(s[1]));
            startYear = minYear + s[0] + 1;
            endYear = minYear + s[1] + 1;
            buildGraph(startYear, endYear);
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


        // Reselect node.
        selectedTopic.forEach(function(topic) {
            cy.$('#' + topic).select();
        });

    }

    var draw = function() {
        var width = parseInt(d3.select('#topic-stream').style('width'), 10),
            height = parseInt(d3.select('#topic-stream').style('height'), 10);

        var x = d3.scale.linear()
            .domain([0, m - 1])
            .range([0, width]);

        var y = d3.scale.linear()
            .domain([0, d3.max(layers, function(layer) {return d3.max(layer.layer, function(d) { return d.y0 + d.y; }); })])
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
            .attr("d", function(d) {
                return area(d.layer);
            })
            .style("fill", function() {
                return color[Math.floor(Math.random() * color.length)];
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
            .attr("height", height - 1);

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
        }

        function brushend() {
            var s = brush.extent();
            s = [Math.round(s[0]), Math.round(s[1])];
            console.log(s);
            if (s[0] == s[1]) s[1] += 1;
            // brush.extent(s);
            d3.select(this).transition()
                .call(brush.extent(s));

            muteLeft.transition()
                .attr("width", x(s[0]));
            muteRight.transition()
                .attr('x', x(s[1]))
                .attr('width', width - x(s[1]));
            buildGraph(minYear + s[0], minYear + s[1]);
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

    var resize = function() {
        redraw();
    }






    // First load the map, then load the time-stream, then load the graph.
    // map.on('style.load', function() {
        d3.json("/topics/?data=time", function(data) {
            data.topics.forEach(function(elem) {
                var theseWeights = [];
                elem.dates.forEach(function(date, i) {
                    theseWeights.push({
                        'date': date,
                        'value': elem.values[i]
                    });
                });
                topicWeights[elem.topic] = theseWeights;
            });

            n = data.topics.length
            m = data.topics[0].values.length; // number of samples per layer

            var dataLayer = function(dt) {
                var a = [], i;
                for (i = 0; i < m; ++i) a[i] = 0;

                var series = a.map(function(d, i) {

                    return {
                        x: i,
                        y0: 0,
                        y: data.topics[dt].values[i]
                    };
                });
                return series;
            }
            layers = stack(d3.range(data.topics.length).map(function(dt) { return dataLayer(dt); })).map(function(l, i) { return {t: i, layer:l }; });

            years = data.topics[0].dates;
            draw(layers);

            d3.select(window).on('resize', resize);

            buildGraph(startYear, endYear);

        });
    // });


});
