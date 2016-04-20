// Provide your access token
mapboxgl.accessToken = 'pk.eyJ1IjoiZXJpY2twZWlyc29uIiwiYSI6ImNpbjIzOHVpMjBiY3l2cWx1b2syaXZnemkifQ.7_5I3_PzXo9gbdS8v1o97A';

var map = new mapboxgl.Map({
    container: 'map', // container id
    style: 'mapbox://styles/erickpeirson/cin20zapx005pafncyt65cgx9', //stylesheet location
    center: [-5, 40], // starting position
    zoom: 1,
    minZoom: 1,
    maxZoom: 7,
});

map.on('style.load', function(){
    var dataLocation = dataLocationURL + '&start=' + start + '&end=' + end;

    if (topic != "None" & topic != "") {
        dataLocation += '&topic=' + topic;
    }

    // Add a new source from our GeoJSON data and set the
    // 'cluster' option to true.
    map.addSource("articles", {
        type: "geojson",
        // Point to GeoJSON data. This example visualizes all M1.0+ earthquakes
        // from 12/22/15 to 1/21/16 as logged by USGS' Earthquake hazards program.
        data: dataLocation,
        cluster: true,
        clusterMaxZoom: 14, // Max zoom to cluster points on
        clusterRadius: 50 // Radius of each cluster when clustering points (defaults to 50)
    });

    map.addLayer({
        "id": "non-cluster-markers",
        "type": "symbol",
        "source": "articles",
        "layout": {
            "icon-image": "circle-15",
        }
    });

    var layers = [
        [150, 'rgb(17, 119, 136)'],
        [20, 'rgb(168, 26, 0)'],
        [0, 'rgb(153, 102, 34)']
    ];

    layers.forEach(function (layer, i) {
        map.addLayer({
            "id": "cluster-" + i,
            "type": "circle",
            "source": "articles",
            "paint": {
                "circle-color": layer[1],
                "circle-radius": 18
            },

            "filter": i == 0 ?
                [">=", "point_count", layer[0]] :
                ["all",
                    [">=", "point_count", layer[0]],
                    ["<", "point_count", layers[i - 1][0]]]
        });
    });

    // Add a layer for the clusters' count labels
    map.addLayer({
        "id": "cluster-count",
        "type": "symbol",
        "source": "articles",
        "layout": {
            "text-field": "{point_count}",
            "text-font": [
                    "DIN Offc Pro Medium",
                    "Arial Unicode MS Bold"
                ],
            "text-size": 12
        }
    });
});

map.on('click', function (e) {
    // Select only non-cluster points.
    var features = map.queryRenderedFeatures(e.point, {filter: ["==", "class", "location"]});

    if (!features.length) {
        return;
    }

    var feature = features[0];

    $('#document-list').empty();
    $('#document-list-panel').css('visibility', 'visible');
    $('#document-list-heading-label').text(feature.properties.label);
    $.get('/locations/' + feature.properties.id + '/?data=json', {}, function(data) {
        data.documents.forEach(function(doc) {
            $('#document-list').append(
                '<tr class="h6">' +
                    '<td>' + doc.date + '</td>'+
                    '<td><a href="/documents/'+ doc.id +'/">' + doc.title + '</a></td>' +
                '</tr>'
            );
        });
    });
});

var popup = new mapboxgl.Popup({
    closeButton: false,
    closeOnClick: false
});

map.on('mousemove', function (e) {
    var features = map.queryRenderedFeatures(e.point, {filter: ["==", "class", "location"]});
    map.getCanvas().style.cursor = (features.length) ? 'pointer' : '';

    if (!features.length) {
        popup.remove();
        return;
    }

    var feature = features[0];

    // Populate the popup and set its coordinates
    // based on the feature found.
    popup.setLngLat(feature.geometry.coordinates)
        .setHTML(feature.properties.label)
        .addTo(map);
});
