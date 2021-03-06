var minYear = 1968,
    maxYear = 2017;

var svg,
    brush,
    muteLeft,
    muteRight,
    brushg,
    brushPos = [(maxYear-minYear)-(maxYear-startYear), (maxYear-minYear)-(maxYear-endYear)],
    years,
    m,
    n=20,
    resizeTree,
    stack = d3.layout.stack().offset("wiggle");

var color = ["#AA9A66", "#B74934", "#221100", "#577492", "#67655D", "#332C2F", "#A81A00", "#4C3F3D", "#996622", "#117788",
             "#AA9A66", "#B74934", "#221100", "#577492", "#67655D", "#332C2F", "#A81A00", "#4C3F3D", "#996622", "#117788",
             "#AA9A66", "#B74934", "#221100", "#577492", "#67655D", "#332C2F", "#A81A00", "#4C3F3D", "#996622", "#117788"];
var thisColor = color[Math.floor(Math.random() * color.length)];

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
        .interpolate("basis")
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

    function brushmove() {
        brushPos = brush.extent();

        muteLeft.attr('width', x(brushPos[0]));
        muteRight.attr('x', x(brushPos[1]));
        muteRight.attr('width', width - x(brushPos[1]));
    }

    function brushend() {
        var s = [Math.round(brush.extent()[0]), Math.round(brush.extent()[1])];
        if (s[0] == s[1]) s[1] += 1;
        d3.select(this).transition()
            .call(brush.extent(s));

        muteLeft.transition()
            .attr("width", x(s[0]));
        muteRight.transition()
            .attr('x', x(s[1]))
            .attr('width', width - x(s[1]));
        startYear = minYear + s[0];
        endYear = minYear + s[1];

        refreshOrganismData(startYear, endYear);
        svg.classed("selecting", !d3.event.target.empty());
    }

    brush.x(x)
        .extent(brushPos)
        .on("brushstart", brushstart)
        .on("brush", brushmove)
        .on("brushend", brushend);


    brushPos = brush.extent();

    muteLeft.attr('width', x(brushPos[0]));
    muteRight.attr('x', x(brushPos[1]));
    muteRight.attr('width', width - x(brushPos[1]));

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
        .interpolate("basis")
        .x(function(d) { return x(d.x); })
        .y0(function(d) { return y(d.y0); })
        .y1(function(d) { return y(d.y0 + d.y); });

    var axis = d3.svg.axis()
        .scale(x)
        .orient("top")
        .tickFormat(function(d, i) {
            return String(years[d]);
        });

    svg = d3.select("#topic-stream")
        .append("svg")
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
    refreshOrganismData(startYear, endYear);

    function brushstart() {
        svg.classed("selecting", true);
    }

    function brushmove() {
        brushPos = brush.extent();;

        muteLeft.attr('width', x(brushPos[0]));
        muteRight.attr('x', x(brushPos[1]));
        muteRight.attr('width', width - x(brushPos[1]));
    }

    function brushend() {
        var s = [Math.round(brush.extent()[0]), Math.round(brush.extent()[1])];
        if (s[0] == s[1]) s[1] += 1;
        d3.select(this).transition()
            .call(brush.extent(s));

        muteLeft.transition()
            .attr("width", x(s[0]));
        muteRight.transition()
            .attr('x', x(s[1]))
            .attr('width', width - x(s[1]));

        startYear = minYear + s[0];
        endYear = minYear + s[1];

        refreshOrganismData(startYear, endYear);
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
    redraw();
    resizeTree();
}

var clearContainingDocuments = function () {
    $('#assignments').empty();
}


var addContainingDocuments = function(data) {
    var assignmentsElem = $('#assignments');
    data.documents.forEach(function(doc) {
        var dateRow = $('<td class="col-xs-1">' + doc.pubdate + '</td>')
        var assignmentLinkRow = $('<td><a href="/documents/' + doc.id + '/">' + doc.title + '</a></td>');
        var progressRow = $('<td class="col-xs-1"><span class="badge">' + doc.weight + '</span></td>');
        var rowElem = $('<tr>');
        rowElem.append(dateRow)
            .append(assignmentLinkRow)
            .append(progressRow);

        assignmentsElem.append(rowElem);
    });
}

// Get documents and related topics.
var refreshOrganismData = function(start, end) {
    var docSpinOpts = {
        lines: 12 // The number of lines to draw
        , length: 10 // The length of each line
        , width: 7 // The line thickness
        , radius: 10 // The radius of the inner circle
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
    $('#assignments').spin(docSpinOpts);
    $.ajax('?data=json&start=' + start + '&end=' + end, {
        success: function(elements) {
            $('#assignments').spin(false);
            clearContainingDocuments();
            addContainingDocuments(elements);

            $('.assignmentQualifier').text(' (' + start + '\u2013' + end + ')');
        }
    });
}

// ``organism_detail_url`` should be set in the template.
if (!organism_detail_url) {
    console.log('Variable ``organism_detail_url`` is not set.')
}

d3.json(organism_detail_url + "?data=time", function(data) {
    n = 20; // number of layers
    m = data.values.length; // number of samples per layer

    var a = [], i;
    for (i = 0; i < m; ++i) a[i] = 0;
    var series = a.map(function(d, i) { return {x: i, y: data.values[i]}; });
    layers = stack([series]);
    years = data.dates;
    draw(layers);
    d3.select(window).on('resize', resize);
});


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
    , top: '60%' // Top position relative to parent
    , left: '50%' // Left position relative to parent
    , shadow: false // Whether to render a shadow
    , hwaccel: false // Whether to use hardware acceleration
    , position: 'absolute' // Element positioning
}

// Show a spinner in the cladogram/tree view until the data is loaded.
$('#tree').spin(opts);

d3.json("?data=tree", function(data) {
    $('#tree').spin(false);

    /**
    * The dimensions of the tree visualization is based on the dimensions of
    #  its parent container.
    */
    resizeTree = function() {
        treeWidth = parseInt(d3.select('#tree').style('width'), 10) - margin.right - margin.left,
        treeHeight = parseInt(d3.select('#tree').style('height'), 10) - margin.top - margin.bottom;

        // Update the layout dimensions.
        tree.size([treeHeight*2, treeWidth]);

        // Scale the tree visualization itself.
        d3.select("#tree>svg").attr("width", treeWidth + margin.right + margin.left)
            .attr("height", treeHeight + margin.top + margin.bottom);
        d3.select("#tree>svg>g").attr("transform", "translate(" + margin.left + "," + -treeHeight/2 + ")");

        // rect is the dragable surface.
        rect.attr("width", treeWidth + margin.right + margin.left)
            .attr("height", treeHeight + margin.top + margin.bottom)

    }
    // d3.select(window).on('resize', resizeTree);

    // Draw the tree for the first time.
    var margin = {top: 20, right: 120, bottom: 20, left: 120},
    treeWidth = parseInt(d3.select('#tree').style('width'), 10) - margin.right - margin.left,
    treeHeight = parseInt(d3.select('#tree').style('height'), 10) - margin.top - margin.bottom;

    var i = 0,
    duration = 750,     // milliseconds; Un/collapse transition duration.
    root;           // We need access to the tree throughout this context.

    var tree = d3.layout.tree()
        .size([treeHeight*2, treeWidth]);

    var diagonal = d3.svg.diagonal()
        .projection(function(d) { return [d.y, d.x]; });

    var treesvg = d3.select("#tree").append("svg")
        .attr("width", treeWidth + margin.right + margin.left)
        .attr("height", treeHeight + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + -treeHeight/2 + ")");

    // Dragable surface.
    var rect = treesvg.append("rect")
        .attr("width", treeWidth + margin.right + margin.left)
        .attr("height", treeHeight + margin.top + margin.bottom)
        .style("fill", "none")
        .style("pointer-events", "all");

    // Nodes and edges go in here.
    var container = treesvg.append('g')
        .attr("transform", "translate(0, 0)");

    var zoom = d3.behavior.zoom()
        .scaleExtent([0.5, 5])
        .on("zoom", zoomed);
    treesvg.call(zoom);
    zoom.scale(0.5);
    zoom.translate([0, treeHeight/2]);
    zoom.event(treesvg);

    root = data.data[0];

    // Position the root of the tree at the far left of the visualization,
    //  centered verticaly.
    root.children.forEach(collapse);
    root.x0 = treeHeight;// / 2;
    root.y0 = 0;
    update(root);   // Transition nodes to their initial positions.

    /**
    *  Swapping .children and ._children controls the display state of the
    #   node (uncollapsed/collapsed).
    */
    function click(d) {
        if (d.children) {
            d._children = d.children;
            d.children = null;
        } else {
            d.children = d._children;
            d._children = null;
        }
        update(d);
    }

    /**
    * Collapse all nodes except those along the path from root to the focal
    *  taxon node.
    */
    function collapse(d) {
        if (d.children) {
            if (data.direct.indexOf(d.id) == -1) {
                d._children = d.children;
                d.children = null;
                d._children.forEach(collapse);
            } else {
                d.children.forEach(collapse);
            }
        }
    }

    /**
    * Absorb the drag event while the user pans.
    */
    function dragstarted(d) {
        d3.event.sourceEvent.stopPropagation();
        d3.select(this).classed("dragging", true);
    }

    function dragged(d) {
        d3.select(this).attr("cx", d.x = d3.event.x).attr("cy", d.y = d3.event.y);
    }

    function dragended(d) {
        d3.select(this).classed("dragging", false);
    }

    /**
    * Execute the zoom.
    */
    function zoomed() {
        container.attr("transform", function() {
            return "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")";
        });
    }

    /**
    *  Transition the tree visualization to a new layout state.
    */
    function update(source) {
        // Compute the new tree layout.
        var nodes = tree.nodes(root).reverse(),
        links = tree.links(nodes);

        // Normalize for fixed-depth.
        nodes.forEach(function(d) { d.y = d.depth * 180; });

        // Update the nodes…
        var node = container.selectAll("g.node")
            .data(nodes, function(d) { return d.id || (d.id = ++i); });

        // Enter any new nodes at the parent's previous position.
        var nodeEnter = node.enter().append("g")
            .attr("class", "node")
            .attr("transform", function(d) { return "translate(" + source.y0 + "," + source.x0 + ")"; })
            .on("click", click);

        nodeEnter.append("circle")
            .attr("r", 1e-6)    // Too small to be seen.
            .style("fill", function(d) {
                // TODO: these colors shouldn't be hard-coded.
                if (d.id == data.focal) {
                    return "#221100";   // The focal taxon node.
                }
                if (d._children) {
                    return "#B74934";   // A collapsed node with children.
                } else {
                    return "#577492";   // An uncollapsed node.
                }
            });

        nodeEnter.append("text")
            .attr("x", function(d) { return d.children || d._children ? -15 : 15; })
            .attr("dy", ".35em")
            .attr("text-anchor", function(d) { return d.children || d._children ? "end" : "start"; })
            .text(function(d) { return d.scientific_name; })
            .style("fill-opacity", 1e-6);

        // The user can click on an icon next to a node to visit the detail
        //  view for that taxon.
        nodeEnter.append('a')
            .attr("xlink:href", function(d) {
                // TODO: This probably shouldn't be hardcoded.
                return "/organisms/" + d.id + "/";
            })
            .append("text")
            .attr("dx", function(d) {
                // Move the icon out of the way of child nodes/edges.
                return d.children || d._children ? 15 : -30;
            })
            .attr("dy", -10)
            .attr("class", "icon")
            .text('\uf0c1')    // FontAwesome link icon.
            .style("fill-opacity", 1e-6);


        // Transition nodes to their new position.
        var nodeUpdate = node.transition()
            .duration(duration)
            .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });

        nodeUpdate.select("circle")
            .attr("r", function(d) { if (d.count > 0) { return 10; } else { return 5; }})
            .style("fill", function(d) { if (d.id == data.focal) { return "#221100"; } else if (d._children) { return "#B74934"; } else { return "#577492"; }});

        nodeUpdate.select("text")
            .style("fill-opacity", 1);

        nodeUpdate.select("a>text.icon")
            .style("fill-opacity", 1);

        // Transition exiting nodes to the parent's new position.
        var nodeExit = node.exit().transition()
            .duration(duration)
            .attr("transform", function(d) { return "translate(" + source.y + "," + source.x + ")"; })
            .remove();

        // We hide the nodes by making them too small to be seen...
        nodeExit.select("circle").attr("r", 1e-6);
        // ...making their labels transparent...
        nodeExit.select("text").style("fill-opacity", 1e-6);
        // ...and making any attendant icons transparent.
        nodeExit.select("a>text.icon").style("fill-opacity", 1e-6);

        // Update the links…
        var link = container.selectAll("path.link")
            .data(links, function(d) { return d.target.id; });

        // Enter any new links at the parent's previous position.
        link.enter().insert("path", "g")
            .attr("class", "link")
            .attr("d", function(d) {
                var o = {x: source.x0, y: source.y0};
                return diagonal({source: o, target: o});
            });

        // Transition links to their new position.
        link.transition()
            .duration(duration)
            .attr("d", diagonal);

        // Transition exiting nodes to the parent's new position.
        link.exit().transition()
            .duration(duration)
            .attr("d", function(d) {
                var o = {x: source.x, y: source.y};
                return diagonal({source: o, target: o});
            })
            .remove();

        // Stash the old positions for transition.
        nodes.forEach(function(d) {
            d.x0 = d.x;
            d.y0 = d.y;
        });


    }


});
