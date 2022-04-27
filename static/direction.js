function initMap() {
    const directionsService = new google.maps.DirectionsService();
    const directionsRenderer = new google.maps.DirectionsRenderer();
    const map = new google.maps.Map(document.getElementById("map"), {
      zoom : 3,
      center: orig,
    });
  
    directionsRenderer.setMap(map);
  
    calculateAndDisplayRoute(directionsService, directionsRenderer);
  }
  
  function calculateAndDisplayRoute(directionsService, directionsRenderer) {
    directionsService
      .route({
        origin: orig,
        destination: dest,
        travelMode: google.maps.TravelMode.DRIVING,
      })
      .then((response) => {
        directionsRenderer.setDirections(response);
      })
      .catch((e) => window.alert("Directions request failed due to " + status));
  }
  
  window.initMap = initMap;