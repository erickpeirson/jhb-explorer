

// Create a map in the div #map
var map = L.mapbox.map('map', null, {minZoom: 1, maxZoom: 7})
    .setView([-5, 40], 1);


/**
  * When the user clicks on a non-cluster marker, display the articles
  *  associated with that location.
  */
var display_articles_for_location = function(e) {
    var feature = e.target.feature;

    $('#document-list').empty();
    $('#document-list-panel').css('visibility', 'visible');
    $('#document-list-heading-label').text(feature.properties.label);
    // TODO: This shouldn't be hardcoded.
    $('#document-list-heading-link').attr('href', 'http://geonames.org/' + feature.properties.id)
        .attr('target', '_blank');
    $.get('/locations/' + feature.properties.id + '/?data=json', {}, function(data) {
        // TODO: use a template.
        data.documents.forEach(function(doc) {
            $('#document-list').append(
                '<tr class="h6" style="border: 0px;">' +
                    '<td>' + doc.date + '</td>'+
                    '<td><a href="/documents/'+ doc.id +'/">' + doc.title + '</a></td>' +
                '</tr>'
            );
        });
    });
}

var styleLayer = L.mapbox.styleLayer('mapbox://styles/erickpeirson/cin20zapx005pafncyt65cgx9')
    .addTo(map);

// TODO: this shouldn't be hard-coded.
var dataLocation = 'http://127.0.0.1:8000/locations/' + dataLocationURL + '&start=' + startYear + '&end=' + endYear;

// Adds clustering behavior to the map.
L.mapbox.featureLayer(dataLocation).on('ready', function(e) {
    var clusterGroup = new L.MarkerClusterGroup({
        showCoverageOnHover: false
    });
    e.target.eachLayer(function(layer) {
        clusterGroup.addLayer(layer);

        // This doesn't get triggered when a user clicks on a cluster; only a
        //  specific marker.
        layer.on('click', display_articles_for_location);
    });
    map.addLayer(clusterGroup);
});
