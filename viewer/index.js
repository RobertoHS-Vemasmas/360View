'use strict';
// Create viewer.
var viewer = new Marzipano.Viewer(document.getElementById('pano'));

// Crear fuente.
var source = Marzipano.ImageUrlSource.fromString(
  "image.jpg"
);

// Crear geometria.
var geometry = new Marzipano.EquirectGeometry([{ width: 8192 }]);

// Crear vista.
var limiter = Marzipano.RectilinearView.limit.traditional(8192, 100*Math.PI/180);
var view = new Marzipano.RectilinearView({ yaw:180*Math.PI/180},limiter);

// Create scene.
var scene = viewer.createScene({
  source: source,
  geometry: geometry,
  view: view,
  pinFirstLevel: true
});

// Escena de visualización.
scene.switchTo();

var viewChangeHandler = function() {
    var yaw = view.yaw();
	var act_yaw=yaw;
	var d_yaw=yaw/(Math.PI/180)
	console.log(d_yaw);
  };
 
view.addEventListener('change', viewChangeHandler);