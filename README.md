<!-- <p align="center">
    <img width="248" height="250" src="https://github.com/RobertoHS-Vemasmas/360View/blob/main/360icon.png" alt=""360 logo">
</p> -->

# 360View
Este plugin permite la visualización de imágenes equirectangulares, se puede utilizar para cualquier imagen 360 dado que se utiliza la libreria Marzipano.

## Requisitos previos
Se requiere la bilioteca Pillow, instalar el paquete Pillow python:

`python3 -m pip install pillow`

Convertir archivos de interfaz de usuario:

`pyuic5 -o output.py ui_orbitalDialog.ui`

Convertir archivos de recursos:

`pyrcc5 icons.qrc -o icons_rc.py`