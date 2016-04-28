

var normalize_weight = function(weight, max_weight) {
    return Math.max(20, 3*weight/max_weight);
}

var color = d3.scale.ordinal()
    .range(["#AA9A66", "#B74934", "#221100", "#577492", "#67655D", "#332C2F", "#A81A00", "#4C3F3D", "#996622", "#117788",
                 "#AA9A66", "#B74934", "#221100", "#577492", "#67655D", "#332C2F", "#A81A00", "#4C3F3D", "#996622", "#117788",
                 "#AA9A66", "#B74934", "#221100", "#577492", "#67655D", "#332C2F", "#A81A00", "#4C3F3D", "#996622", "#117788"]);



var redraw = function (callback) {
    var margin = {top: 0, right: 0, bottom: 0, left: 0},
        width = parseInt(d3.select('#topic-barchart').style('width'), 10) - margin.left - margin.right,
        height = 300 - margin.top - margin.bottom;

    var x = d3.scale.ordinal()
        .rangeRoundBands([0, width], .1);

    var y = d3.scale.linear()
        .rangeRound([height, 0]);


    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
        .tickFormat(d3.format(".2s"));

    var svg = d3.select("#topic-barchart").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    d3.json('?data=chart', function(error, data) {
      if (error) throw error;

      color.domain(data.allTopics);

      var p = 0;
      data.weights.forEach(function(d) {
            var y0 = 0;
            d.topics = color.domain().map(function(name) {
                return {
                    name: name,
                    y0: y0,
                    y1: y0 += +d[name],
                };
            });


            d.total = d.topics[d.topics.length - 1].y1;
            d.page = data.pages[p];
            p += 1
      });


      $('.swatch-static').each(function(i) {
          $(this).css('background-color', color($(this).attr('id').split('-')[1]));
      });


      x.domain(data.pages);
      y.domain([0, d3.max(data.weights, function(d) { return d.total; })]);


      var page = svg.selectAll(".page")
          .data(data.weights)
        .enter().append("g")
          .attr("class", "g")
          .attr("transform", function(d) { return "translate(" + x(d.page) + ",0)"; });

      page.selectAll("rect")
          .data(function(d) {
              return d.topics;
           })
        .enter().append("rect")
          .attr("width", x.rangeBand())
          .attr("y", function(d) {
              return y(d.y1); })
          .attr("height", function(d) { return y(d.y0) - y(d.y1); })
          .attr("topic", function(d) { return d.name;  })
          .classed("topicbar", true)
          .style("fill", function(d) { return color(d.name); })
          .on('mouseover', function(d) {
              d3.selectAll("[topic='" + d.name + "']")
                .classed('highlight', true);
          })
          .on('mouseout', function(d) {
              d3.selectAll("[topic='" + d.name + "']")
                .classed('highlight', false);
          })
          .on('click', function(d) {


              refreshTopicData(d.name);
          });
          if (callback) { callback(data); }
    });
};

    var refreshTopicData = function(topic_id) {
        d3.selectAll(".topicbar.selected")
          .classed("selected", false)
          .classed("highlight", false);
        d3.selectAll("[topic='" + topic_id + "']")
          .classed("selected", true);

        d3.json("/topics/" + topic_id + "/?data=json", function(data) {
            var termlist = d3.select('#topic-details-terms');
            $('#topic-details-terms').empty();
            $('#topic-details-title').empty();

            d3.select('#topic-details')
              .style('visibility', 'visible');

            d3.select('#topic-details-swatch').style('background-color', color(data.id));
            d3.select('#topic-details-heading')
            //    .style('background-image', 'linear-gradient(to bottom,#f5f5f5 0,'+ color(data.id) + ' 100%)');
          d3.select('#topic-details-title')
              .text('Topic details');
          d3.select('#topic-details-link')
              .attr('href', topics_url + data.id + '/');

            var maxWeight = data.terms[0].weight;
            data.terms.forEach(function(term) {
                 termlist.append('li')
                  .classed("topic-details-term", true)
                  .attr("style", "font-size:" + Math.max(0.75, term.weight*2.5) + 'vw;')
                  .text(term.term);
            });
        });
    }
    redraw(function() {
        if (initialTopic) refreshTopicData(initialTopic);
    });

    var resize = function() {
        $('#topic-barchart').empty();
        redraw();
    };

    var windowWidth = $(window).width();
    d3.select(window).on('resize', function(event) {
        var diff = windowWidth - $(window).width();
        if (diff > 10 | diff < -10) {
            resize(event);
            windowWidth = $(window).width();
        }
    })
    d3.select(window).on('orientationchange', function(event) {
        resize(event);
        windowWidth = $(window).width();
    });
