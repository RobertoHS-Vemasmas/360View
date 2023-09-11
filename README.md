# 360View
Este plugin permite la visualización de imágenes equirectangulares, se puede utilizar para cualquier imagen 360 dado que se utiliza la libreria Marzipano.

## Requisitos previos
Se requiere la bilioteca Pillow, instalar el paquete Pillow python:

`python3 -m pip install pillow`

Convertir archivos de interfaz de usuario:

`pyuic5 -o output.py ui_orbitalDialog.ui`

Convertir archivos de recursos:

`pyrcc5 icons.qrc -o icons_rc.py`

Configurar el sistema de coordenadas del proyecto QGIS

Sistema de referencia de coordenadas: `WSG 84`

ID de la autoridad: `EPSG:4326`
