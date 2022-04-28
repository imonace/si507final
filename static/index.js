// This example displays a marker at the center of Australia.
// When the user clicks the marker, an info window opens.
function initMap() {
  const map = new google.maps.Map(document.getElementById("map"), {
    zoom: 14,
    center: loc,
  });
  const infowindow = new google.maps.InfoWindow({
    content: locString,
  });
  const marker = new google.maps.Marker({
    position: loc,
    map,
    title: locTitle,
  });

  //marker.addListener("click", () => {
    infowindow.open({
      anchor: marker,
      map,
      shouldFocus: false,
    });
  //});
}

window.initMap = initMap;