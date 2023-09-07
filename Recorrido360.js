L.Control.Recorrido360 = L.Control.extend({
  options: {
    collapsed: true,
    position: "topleft",
    calculatePosition: false,
    className: "leaflet-control-recorrido360",
    icon: "leaflet-control-recorrido360-icon",
  },

  initialize: function (options) {
    L.Util.setOptions(this, options);
    this._container = L.DomUtil.create(
      "div",
      "leaflet-bar leaflet-control leaflet-control-custom " +
        this.options.className
    );
  },

  onAdd: function (map) {
    var className = this.options.className;
    let container = this._container;
    container.style.backgroundColor = "white";
    container.style.borderRadius = "4px";

    L.DomEvent.disableClickPropagation(container);

    map.on("click", this.onClick, this);

    var form = (this._form = L.DomUtil.create("form", className + "-form"));

    var titulo = document.createElement("p");
    titulo.textContent = "Escriba las coordenadas o haga clic en el mapa";
    titulo.setAttribute("class", className + "-form-title");
    var input_lon = (this._input_lon = document.createElement("input"));
    input_lon.className = className + "-form-input";
    input_lon.name = "lon";
    input_lon.type = "text";
    input_lon.placeholder = "";
    input_lon.autocomplete = "off";
    var label_lon = document.createElement("label");
    label_lon.textContent = "Longitud";
    label_lon.setAttribute("class", className + "-form-label");
    var input_lat = (this._input_lat = document.createElement("input"));
    input_lat.className = className + "-form-input";
    input_lat.name = "lat";
    input_lat.placeholder = "";
    input_lat.autocomplete = "off";
    var label_lat = document.createElement("label");
    label_lat.textContent = "Latitud";
    label_lat.setAttribute("class", className + "-form-label");

    var submit = document.createElement("input");
    submit.type = "submit";
    submit.value = "Abrir vista";
    submit.style.backgroundColor = "#324b84";
    submit.style.fontSize = "12px";
    submit.style.fontWeight = "bold";
    submit.setAttribute("class", className + "-button");
    submit.setAttribute("id", className + "-contact-button");

    var locate = document.createElement("input");
    locate.type = "button";
    locate.value = "Localizar";
    locate.style.backgroundColor = "#324b84";
    locate.style.fontSize = "12px";
    locate.style.fontWeight = "bold";
    locate.setAttribute("class", className + "-button");
    locate.setAttribute("id", className + "-locate-button");
    L.DomEvent.addListener(
      locate,
      L.Browser.touch ? "click" : "focus",
      this._localizarCoordenadas,
      this
    );

    var cancel = document.createElement("input");
    cancel.type = "button";
    cancel.value = "Cancelar";
    cancel.style.backgroundColor = "#324b84";
    cancel.style.fontSize = "12px";
    cancel.style.fontWeight = "bold";
    cancel.setAttribute("class", className + "-button");
    cancel.setAttribute("id", className + "-cancel-button");
    L.DomEvent.addListener(
      cancel,
      L.Browser.touch ? "click" : "focus",
      this._colllapse,
      this
    );

    form.appendChild(titulo);
    form.appendChild(L.DomUtil.create("br"));
    form.appendChild(label_lon);
    form.appendChild(input_lon);
    form.appendChild(L.DomUtil.create("br"));
    form.appendChild(label_lat);
    form.appendChild(input_lat);
    form.appendChild(L.DomUtil.create("br"));
    form.appendChild(L.DomUtil.create("br"));
    form.appendChild(submit);
    form.appendChild(locate);
    form.appendChild(cancel);
    form.appendChild(L.DomUtil.create("br"));
    L.DomEvent.addListener(form, "submit", this._abrirRecorrido, this);
    form.appendChild(L.DomUtil.create("br"));

    if (this.options.collapsed) {
      var button = (this._layersButton = L.DomUtil.create(
        "a",
        className + " " + this.options.icon,
        container
      ));
      button.title = "Abrir recorrido 360";
      button.style.backgroundImage = "url(shape/assets/360-degrees.png)";
      button.style.backgroundSize = "18px 18px";
      button.style.backgroundPosition = "center";
      button.style.backgroundRepeat = "no-repeat";

      L.DomEvent.addListener(
        button,
        L.Browser.touch ? "click" : "focus",
        this._expand,
        this
      );
    }

    container.appendChild(form);

    return container;
  },
  onClick: function (e) {
    if (this.options.calculatePosition) {
      var lng = this.options.lngFormatter
        ? this.options.lngFormatter(e.latlng.lng)
        : L.Util.formatNum(e.latlng.lng, this.options.numDigits);
      var lat = this.options.latFormatter
        ? this.options.latFormatter(e.latlng.lat)
        : L.Util.formatNum(e.latlng.lat, this.options.numDigits);
      this._input_lon.value = lng;
      this._input_lat.value = lat;
      this._removerMarcador();
      var newMarker = (this.options._marker = new L.CircleMarker([lat, lng]));
      newMarker.addTo(this._map);
    }
  },
  _expand: function () {
    this.options.calculatePosition = true;
    L.DomUtil.addClass(
      this._container,
      "leaflet-control-recorrido360-expanded"
    );
  },
  _colllapse: function () {
    this.options.calculatePosition = false;
    this._container.className = this._container.className.replace(
      " leaflet-control-recorrido360-expanded",
      ""
    );
    this._removerMarcador();
  },
  _abrirRecorrido: function (event) {
    L.DomEvent.preventDefault(event);
    enviarCoordenadas(this._input_lon.value, this._input_lat.value, this);
  },
  // _localizarCoordenadas: function () {
  //   var lat = parseFloat(this._input_lat.value);
  //   var lon = parseFloat(this._input_lon.value);
  //   if (isNaN(lat) || isNaN(lon)) {
  //     alert("Formato de coordenadas inválido");
  //   } else {
  //     map.setView([lat, lon]);
  //     this._removerMarcador();
  //     var newMarker = this.options._marker = new L.CircleMarker([lat, lon]);
  //     newMarker.addTo(this._map);
  //   }
  // },
  _localizarCoordenadas: function () {
    var lat = parseFloat(this._input_lat.value);
    var lon = parseFloat(this._input_lon.value);
    if (isNaN(lat) || isNaN(lon)) {
      // alert("Formato de coordenadas inválido");
      const swalWithBootstrapButtons = Swal.mixin({
        customClass: {
          confirmButton: "btn btn-success",
          cancelButton: "btn btn-danger",
        },
        buttonsStyling: true,
      });
      swalWithBootstrapButtons.fire({
        title: "Formato de coordenadas inválido",
        icon: "error",
        confirmButtonColor: "#324b84",
        confirmButtonText: "Aceptar",
        showClass: {
          popup: "animate__animated animate__fadeInDown",
        },
        hideClass: {
          popup: "animate__animated animate__fadeOutUp",
        },
      });
    } else {
      map.setView([lat, lon]);
      this._removerMarcador();
      var newMarker = (this.options._marker = new L.CircleMarker([lat, lon]));
      newMarker.addTo(this._map);
    }
  },
  _removerMarcador: function () {
    if (this.options._marker !== undefined) {
      map.removeLayer(this.options._marker);
      this.options._marker = undefined;
    }
  },
});

// function enviarCoordenadas(lon, lat, control) {
//   lon = parseFloat(lon);
//   lat = parseFloat(lat);
//   if (isNaN(lon) || isNaN(lat)) {
//     alert("Formato de coordenadas inválido");
//     return;
//   }
//   var settings = {
//     "url": "http://localhost:8000/recorridos360/existenRecorridos",
//     "method": "POST",
//     "timeout": 0,
//     "headers": {
//       "Content-Type": "application/json"
//     },
//     "data": JSON.stringify({
//       "latitud": lat,
//       "longitud": lon,
//     }),
//   };
//   $.ajax(settings)
//     .done(function (response) {
//       if (response.cantidadRecorridos === 0) {
//         alert("No se encontraron recorridos cercanos a estas coordenadas");
//       } else {
//         coordenadasRecorrido = [lat, lon];
//         Vista360.options.container.click();
//         control._colllapse();
//       }
//     })
//     .fail(function (jqXHR, textStatus) {
//       alert("No fue posible conectarse al servidor");
//     });
// }

function enviarCoordenadas(lon, lat, control) {
  lon = parseFloat(lon);
  lat = parseFloat(lat);
  if (isNaN(lon) || isNaN(lat)) {
    const swalWithBootstrapButtons = Swal.mixin({
      customClass: {
        confirmButton: "btn btn-success",
        cancelButton: "btn btn-danger",
      },
      buttonsStyling: true,
    });
    // alert("Formato de coordenadas inválido");
    swalWithBootstrapButtons.fire({
      title: "Formato de coordenadas inválido",
      icon: "error",
      confirmButtonColor: "#324b84",
      confirmButtonText: "Aceptar",
      showClass: {
        popup: "animate__animated animate__fadeInDown",
      },
      hideClass: {
        popup: "animate__animated animate__fadeOutUp",
      },
    });
    return;
  }
  var settings = {
    // url: "http://localhost:8000/recorridos360/existenRecorridos",
    // url: "https://pruebas.grupotum.com:8443/ideeqro_api/recorridos360/existenRecorridos",
    url: "https://10.16.106.74/ideeqro_api/recorridos360/existenRecorridos",
    method: "POST",
    timeout: 0,
    headers: {
      "Content-Type": "application/json",
    },
    data: JSON.stringify({
      latitud: lat,
      longitud: lon,
    }),
  };
  $.ajax(settings)
    .done(function (response) {
      if (response.cantidadRecorridos === 0) {
        const swalWithBootstrapButtons = Swal.mixin({
          customClass: {
            confirmButton: "btn btn-success",
            cancelButton: "btn btn-danger",
          },
          buttonsStyling: true,
        });
        // alert("No se encontraron recorridos cercanos a estas coordenadas");
        swalWithBootstrapButtons.fire({
          title: "No se encontraron recorridos cercanos a estas coordenadas",
          icon: "info",
          confirmButtonColor: "#324b84",
          confirmButtonText: "Aceptar",
          showClass: {
            popup: "animate__animated animate__fadeInDown",
          },
          hideClass: {
            popup: "animate__animated animate__fadeOutUp",
          },
        });
      } else {
        coordenadasRecorrido = [lat, lon];

        var settings = {
          // url: "http://localhost:8000/recorridos360/obtenerRecorridos",
          // url: "https://pruebas.grupotum.com:8443/ideeqro_api/recorridos360/obtenerRecorridos",
          url: "https://10.16.106.74/ideeqro_api/recorridos360/obtenerRecorridos",
          method: "POST",

          timeout: 0,
          headers: {
            "Content-Type": "application/json",
          },
          data: JSON.stringify({
            latitud: parseFloat(lat),
            longitud: parseFloat(lon),
          }),
        };
        $.ajax(settings)
          .done(function (response) {
            if (response.cantidadRecorridos === 0) {
              alert(response.error);
            } else {
              const infoPuntos = response;
              crearVista(infoPuntos);
            }
          })
          .fail(function (jqXHR, textStatus) {
            console.log(textStatus, jqXHR);
            alert("No fue posible conectarse al servidor");
          });

        control._colllapse();
      }
    })
    .fail(function (jqXHR, textStatus) {
      const swalWithBootstrapButtons = Swal.mixin({
        customClass: {
          confirmButton: "btn btn-success",
          cancelButton: "btn btn-danger",
        },
        buttonsStyling: true,
      });
      // alert("No fue posible conectarse al servidor");
      swalWithBootstrapButtons.fire({
        title: "No fue posible conectarse al servidor",
        icon: "error",
        confirmButtonColor: "#324b84",
        confirmButtonText: "Aceptar",
        showClass: {
          popup: "animate__animated animate__fadeInDown",
        },
        hideClass: {
          popup: "animate__animated animate__fadeOutUp",
        },
      });
    });
}

function agregarPunto(lat, lon) {
  var newMarker = new L.CircleMarker([lat, lon]);
  newMarker.bindPopup("Longitud: " + lon + "<br>Latitud: " + lat);
  newMarker.addTo(map);
}

var coordenadasRecorrido;

function crearVista(infoPuntos) {
  var puntoInicial = infoPuntos.puntoInicial;

  var puntos = infoPuntos.puntos;
  var scenesPanorama = {};
  for (var i = 0; i < puntos.length; i++) {
    var imagenNombre = puntos[i].imagen;
    if (!imagenNombre.endsWith(".jpg")) {
      imagenNombre = imagenNombre + ".jpg";
    }
    scenesPanorama[puntos[i].imagen] = {
      type: "equirectangular",
      pitch: 0,
      panorama:
        "https://10.16.106.74/geo/360/" +
        // "https://10.0.1.8/geo/360/" +
        // "https://cartografia.grupotum.com:8543/geo/360/" +
        puntos[i].zona +
        "/" +
        puntos[i].recorrido +
        "/" +
        imagenNombre,
      strings: {
        loadButtonLabel: "Click para\nCargar\nPanorama",
        loadingLabel: "Cargando...",
        bylineLabel: "Realizado por: %s",

        noPanoramaError: "No se especificó una imagen panoramica.",
        fileAccessError: "No se pudo acceder al archivo %s.",
        malformedURLError: "Hay algún error con la URL del panorama.",
        iOS8WebGLError:
          "Debido a la implementación rota de WebGL en iOS, solo JPEGs codificados progresivamente son compatibles con tu dispositivo (este panorama usa codificación estandar).",
        genericWebGLError:
          "Tu navegador no cuenta con el soporte necesario de WebGL para mostrar este panorama.",
        textureSizeError:
          "Este panorama es demasiado grande para tu dispositivo! Tiene %spx de ancho, pero tu dispositivo solo soporta imagenes de hasta %spx de ancho. Intenta con otro dispositivo. (Si usted es el autor, intente disminuir el tamaño.)",
        unknownError: "Error desconocido. Revise la consola de desarrollador.",
      },
      hotSpots: [],
    };
    if (i !== 0 && puntos.length > 0) {
      scenesPanorama[puntos[i].imagen].hotSpots.push({
        pitch: 0,
        yaw: 0,
        type: "scene",
        sceneId: puntos[i - 1].imagen,
        targetYaw: 0,
        targetPitch: 0,
      });
    }
    if (i + 1 !== infoPuntos.puntos.length && puntos.length > 0) {
      scenesPanorama[puntos[i].imagen].hotSpots.push({
        pitch: 0,
        yaw: 180,
        type: "scene",
        sceneId: puntos[i + 1].imagen,
        targetYaw: 180,
        targetPitch: 0,
      });
    }
  }

  var mapa = document.getElementById("map");
  const ventana = document.createElement("div");
  ventana.style.position = "absolute";
  ventana.style.zIndex = "1000";
  ventana.style.backgroundColor = "rgba(0,0,0,0.0)";
  ventana.style.height = "40%";
  ventana.style.width = "40%";
  ventana.style.top = "52%";

  // ventana.onclick = function () {
  //   mapa.removeChild(ventana);
  // };

  const panorama = document.createElement("div");
  panorama.id = "panorama";
  panorama.style.height = "100%";
  panorama.style.width = "100%";
  //coordenadasRecorrido guardado previamente desde Recorrido360.js

  const btnCerrar = document.createElement("button");

  btnCerrar.textContent = "Cerrar";
  btnCerrar.style = `position: absolute; right: 9px; top: 15px; border-radius: 4px; 
                     background-color: #4d505f; border: none; color: #FFFFFF;
                     width: 52px; height: 22px; font-size: 13px; z-index: 99;`;

  ventana.appendChild(btnCerrar);
  ventana.appendChild(panorama);

  btnCerrar.addEventListener("click", () => {
    mapa.removeChild(ventana);
  });

  mapa.appendChild(ventana);

  L.DomEvent.disableClickPropagation(ventana);
  L.DomEvent.disableScrollPropagation(ventana);

  pannellum.viewer("panorama", {
    default: {
      firstScene: puntoInicial.imagen,
      // author: "V++",
      autoLoad: true,
    },

    scenes: scenesPanorama,
  });
}
