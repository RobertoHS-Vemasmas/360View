from qgis.core import Qgis as QGis
from qgis.gui import QgsRubberBand
from qgis.utils import iface
from .log import log
from qgis.core import (
    QgsPointXY,
    QgsProject,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsRectangle)


class qgsutils(object):
    @staticmethod
    def convertProjection(x, y, from_crs, to_crs):
        """ Convertir a coordenadas EPSG """
        crsSrc = QgsCoordinateReferenceSystem(from_crs)
        crsDest = QgsCoordinateReferenceSystem(to_crs)
        xform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
        pt = xform.transform(QgsPointXY(x, y))
        return pt

    @staticmethod
    def getAttributeFromFeature(feature, columnName):
        """ Obtener atributo de la característica """
        return feature.attribute(columnName)

    @staticmethod
    def zoomToFeature(canvas, layer, ide):
        """ Acercar a función por ID """
        if layer:
            for feature in layer.getFeatures():
                if feature.id() == ide:
                    # Transform Point
                    actualPoint = feature.geometry().asPoint()
                    projPoint = qgsutils.convertProjection(
                        actualPoint.x(),
                        actualPoint.y(),
                        layer.crs().authid(),
                        canvas.mapSettings().destinationCrs().authid(),
                    )
                    x = projPoint.x()
                    y = projPoint.y()
                    rect = QgsRectangle(x, y, x, y)
                    canvas.setExtent(rect)
                    canvas.refresh()
                    return True
        return False

    @staticmethod
    def showUserAndLogMessage(
        before, text="", level=QGis.Info, duration=3, onlyLog=False
    ):
        """ Mostrar información de usuario y registro/advertencia/mensaje de error """
        if not onlyLog:
            iface.messageBar().popWidget()
            iface.messageBar().pushMessage(before, text, level=level, duration=duration)
        if level == QGis.Info:
            log.info(text)
        elif level == QGis.Warning:
            log.warning(text)
        elif level == QGis.Critical:
            log.error(text)
        return

    @staticmethod
    def getToFeature(layer, ide):
        """ ir a caracrterística por ID """
        if layer:
            for feature in layer.getFeatures():
                if feature.id() == ide:
                    return feature
        return False