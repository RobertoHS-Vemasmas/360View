import math
import os
from qgis.core import QgsPointXY, QgsProject, QgsFeatureRequest,QgsVectorLayer, QgsWkbTypes
from qgis.gui import QgsRubberBand
from qgis.PyQt.QtCore import Qt, pyqtSignal, QUrl, QJsonDocument, QObject, QByteArray

from qgis.PyQt.QtWidgets import QDialog, QWidget, QDockWidget
from qgis.PyQt.QtGui import QWindow
from . import config
from .geom.transformgeom import transformGeometry
from  .ui.output_ui  import Ui_orbitalDialog
from .utils.qgsutils import qgsutils
from qgis.PyQt.QtWebKitWidgets import QWebView, QWebPage
from qgis.PyQt.QtWebKit import QWebSettings
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkRequest, QNetworkAccessManager, QNetworkReply, QSslSocket

try:
    from PIL import Image
except ImportError:
    None

from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager
class _ViewerPage(QWebPage):
    obj = []  # Sincrónico
    newData = pyqtSignal(list)  # Asincrónico

    def javaScriptConsoleMessage(self, msg, line, source):
        l = msg.split(",")
        self.obj = l
        self.newData.emit(l)


class Geo360Dialog(QDockWidget, Ui_orbitalDialog):

    """ Geo360 Dialog Class """

    def __init__(self, iface, parent=None, x=None, y=None):

        QDockWidget.__init__(self)

        self.setupUi(self)

        self.DEFAULT_URL = (f"http://{config.IP}:{str(config.PORT)}/viewer.html")
        self.DEFAULT_EMPTY = (f"http://{config.IP}:{str(config.PORT)}/none.html")
        self.DEFAULT_BLANK = (f"http://{config.IP}:{str(config.PORT)}/blank.html")

        # Crear vista
        self.CreateViewer()

        self.plugin_path = os.path.dirname(os.path.realpath(__file__))
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.parent = parent

        # Orientación de la imagen
        self.yaw = math.pi  # No hace nada
        self.bearing = None

        self.x = x
        self.y = y

        self.actualPointDx = None
        self.actualPointSx = None
        self.actualPointOrientation = None

        # Obtener la ruta de la imagen.
        self.GetImage()
        self.current_image = self.GetImage()

        # Comprobar si existe la imagen
        if not os.path.exists(self.current_image):
            qgsutils.showUserAndLogMessage(
                u"Información: ", u"No existe imagen asociada."
            )
            self.resetQgsRubberBand()
            self.ChangeUrlViewer(self.DEFAULT_EMPTY)
            return

        # Copiar el archivo al servidor local
        self.CopyFile(self.current_image)

        # Establecer RubberBand
        self.resetQgsRubberBand()
        self.setOrientation()
        self.setPosition()

        self.setOrientation(yaw=-45)

    def onNewData(self, data):
        try:
            newYaw = float(data[0])
            self.UpdateOrientation(yaw=newYaw)
        except:
            None

    def CreateViewer(self):
        """ Crear visor """
        qgsutils.showUserAndLogMessage(
            u"Información: ", u"Crear visor", onlyLog=True
        )

        self.cef_widget = QWebView()
        self.cef_widget.setContextMenuPolicy(Qt.NoContextMenu)

        pano_view_settings = self.cef_widget.settings()
        pano_view_settings.setAttribute(QWebSettings.JavascriptEnabled, True)
        pano_view_settings.setAttribute(QWebSettings.WebGLEnabled, True)
        pano_view_settings.setAttribute(QWebSettings.Accelerated2dCanvasEnabled, True)
        pano_view_settings.setAttribute(QWebSettings.JavascriptEnabled, True)

        self.page = _ViewerPage()
        self.page.newData.connect(self.onNewData)
        self.cef_widget.setPage(self.page)

        self.cef_widget.load(QUrl(self.DEFAULT_URL))
        self.ViewerLayout.addWidget(self.cef_widget, 1, 0)

    def RemoveImage(self):
        """ Quitar imagen """
        try:
            os.remove(self.plugin_path + "/viewer/image.jpg")
        except OSError:
            pass

    def CopyFile(self, src):
        """ Copiar archivo de imagen en servidor local """
        qgsutils.showUserAndLogMessage(
            u"Información: ", u"Copiando imagen", onlyLog=True
        )

        src_dir = src
        dst_dir = self.plugin_path + "/viewer"

        # Copiar imagen en carpeta local.
        img = Image.open(src_dir)
        rgb_im = img.convert("RGB")
        dst_dir = dst_dir + "/image.jpg"

        try:
            os.remove(dst_dir)
        except OSError:
            pass

        rgb_im.save(dst_dir)

    def GetImage(self):
        """ Obtener la imagen seleccionada """

        json = {'latitud' : self.x, 'Longitud' : self.y}
        document = QJsonDocument(json)
        print(document.toJson())
 
        # data = QByteArray()
        # data.append(b'latitud=' + str(self.x) + '&amp;')
        # data.append(b'longitud=' + str(self.y))
        # print(data)

        req = QNetworkRequest(QUrl('https://10.16.106.74/ideeqro_api/recorridos360/existenRecorridos'))
        req.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader,
        'application/json')
        print(req)

        conf = req.sslConfiguration()
        conf.setPeerVerifyMode(QSslSocket.VerifyNone)
        req.setSslConfiguration(conf)

        self.nam = QNetworkAccessManager()
        self.nam.finished.connect(self.handleResponse)
        self.nam.post(req, document.toJson())

        print(self.nam)


    def handleResponse(self, reply):

        er = reply.error()

        if er == QNetworkReply.NetworkError.NoError:
            bytes_string = reply.readAll()
            print(bytes_string)

            req = QNetworkRequest(QUrl('https://10.16.106.74/ideeqro_api/recorridos360/obtenerRecorridos'))
            req.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader,
            'application/json')

            self.nam = QNetworkAccessManager()
            self.nam.finished.connect(self.handleRecorrido)
            self.nam.post(req, bytes_string)
            
        else:
            qgsutils.showUserAndLogMessage(
                u"Error: ", reply.errorString()
            )

    def handelRecorrdio(self, reply):
        er = reply.error()

        if er == QNetworkReply.NetworkError.NoError:
            bytes_string = reply.readAll()
            jsonO = QJsonDocument.fromJson(bytes_string)
            puntos = jsonO['puntos'].toArray()
            punto = puntos[0].toObject()

            imagenNombre = punto['imagen']

            if imagenNombre.toString().endswith('.jpg'):
                 imagenNombre = imagenNombre + ".jpg"

            self.path = 'https://10.16.106.74/geo/360/' + punto['zona'] + "/" + punto['recorrido'] + "/" + imagenNombre,

            self.current_image = self.path

            qgsutils.showUserAndLogMessage(
                u"Información: ", str(self.path), onlyLog=True
            )


        else:
            qgsutils.showUserAndLogMessage(
                u"Error: ", reply.errorString()
            )

    def ChangeUrlViewer(self, new_url):
        """Cambiar visor de URL"""
        self.cef_widget.load(QUrl(new_url))

    def ReloadView(self, newId):
        """ Recargar visor de imágenes """
        self.setWindowState(
            self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)

        #  Activará la ventana
        self.activateWindow()
        self.selected_features = qgsutils.getToFeature(self.layer, newId)
        self.showFullScreen()
        self.current_image = self.GetImage()

        # Comprobar si existe la imagen
        print("Value of self.current_image:", self.current_image)
        if not os.path.exists(self.current_image):
            qgsutils.showUserAndLogMessage(
                u"Información: ", u"No existe imagen asociada."
            )
            self.ChangeUrlViewer(self.DEFAULT_EMPTY)
            self.resetQgsRubberBand()
            return

        # Establecer RubberBand
        self.resetQgsRubberBand()
        self.setOrientation(yaw=45)
        self.setPosition()

        # Copiar arcivo al servidor local
        self.CopyFile(self.current_image)

        self.ChangeUrlViewer(self.DEFAULT_URL)

    def GetBackNextImage(self):
        """ Ir a la imagen de atrás """
        sender = QObject.sender(self)

        lys = self.canvas.layers()  # Comprobar si la foto está cargada
        if not lys:
            qgsutils.showUserAndLogMessage(
                u"Información: ", u"Necesita cargar la capa de fotos."
            )
            return

        for layer in lys:
            if layer.name() == config.layer_name:
                self.encontrado = True
                self.iface.setActiveLayer(layer)

                f = self.selected_features

                ac_lordem = f.attribute(config.column_order)

                if sender.objectName() == "btn_back":
                    new_lordem = int(ac_lordem) - 1
                else:
                    new_lordem = int(ac_lordem) + 1

                # Filtar la capa de datos del mapa
                ids = [
                    feat.id()
                    for feat in layer.getFeatures(
                        QgsFeatureRequest().setFilterExpression(
                            f"{config.column_order} ='{str(new_lordem)}'"
                        )
                    )
                ]

                if not ids:
                    qgsutils.showUserAndLogMessage(
                        u"Información: ", u"Sin imagen."
                    )
                    # Filtar la capa de datos del mapa
                    ids = [
                        feat.id()
                        for feat in layer.getFeatures(
                            QgsFeatureRequest().setFilterExpression(
                                f"{config.column_order} ='{str(ac_lordem)}'"
                            )
                        )
                    ]
                #  Actualizar función seleccionada
                self.ReloadView(ids[0])

        if not self.encontrado:
            qgsutils.showUserAndLogMessage(
                u"Información: ",
                u"Necesita una capa con imágenes y establecer el nombre en el archivo config.py"
            )
        return

    def FullScreen(self, value):
        """ Botón de acción de pantalla completa """
        qgsutils.showUserAndLogMessage(
            u"Información: ", u"Pantalla completa.", onlyLog=True
        )
        if value:
            self.showFullScreen()
        else:
            self.showNormal()

    def UpdateOrientation(self, yaw=None):
        """ Actualizar orientación """
        self.bearing = self.selected_features.attribute(config.column_yaw)
        try:
            self.actualPointOrientation.reset()
        except Exception:
            pass

        self.actualPointOrientation = QgsRubberBand(
            self.iface.mapCanvas(), QgsWkbTypes.LineGeometry
        )
        # Indicador azul de posicionamiento en el mapa.
        self.actualPointOrientation.setColor(Qt.blue)
        self.actualPointOrientation.setWidth(2)
        self.actualPointOrientation.addPoint(self.actualPointDx)

        # End Point
        CS = self.canvas.mapUnitsPerPixel() * 15  # Determina el tamaño del puntero
        A1x = self.actualPointDx.x() - CS * math.cos(math.pi / 2)
        A1y = self.actualPointDx.y() + CS * math.sin(math.pi / 2)

        self.actualPointOrientation.addPoint(
            QgsPointXY(float(A1x), float(A1y)))

        # Ángulo de visión
        if yaw is not None:
            angle = float(self.bearing + yaw) * math.pi / -180  # Velocidad de giro (línea azul)
        else:
            angle = float(self.bearing) * math.pi / -180  

        tmpGeom = self.actualPointOrientation.asGeometry()

        self.actualPointOrientation.setToGeometry(
            self.rotateTool.rotate(
                tmpGeom, self.actualPointDx, angle),
            self.dumLayer
        )

    def setOrientation(self, yaw=None):
        """ Establecer la orientación en la primera vez """
        self.bearing = self.selected_features.attribute(config.column_yaw)

        originalPoint = self.selected_features.geometry().asPoint()
        self.actualPointDx = qgsutils.convertProjection(
            self.x,
            self.y,
            self.layer.crs().authid(),
            self.canvas.mapSettings().destinationCrs().authid(),
        )

        self.actualPointOrientation = QgsRubberBand(
            self.iface.mapCanvas(), QgsWkbTypes.LineGeometry
        )
        self.actualPointOrientation.setColor(Qt.blue)
        self.actualPointOrientation.setWidth(3)

        self.actualPointOrientation.addPoint(self.actualPointDx)

        # End Point
        CS = self.canvas.mapUnitsPerPixel() * 15
        A1x = self.actualPointDx.x() - CS * math.cos(math.pi / 2)
        A1y = self.actualPointDx.y() + CS * math.sin(math.pi / 2)

        self.actualPointOrientation.addPoint(
            QgsPointXY(float(A1x), float(A1y)))

        # Ángulo de visión
        if yaw is not None:
            angle = float(self.bearing + yaw) * math.pi / -180
        else:
            angle = float(self.bearing) * math.pi / -180

        tmpGeom = self.actualPointOrientation.asGeometry()

        self.rotateTool = transformGeometry()
        epsg = self.canvas.mapSettings().destinationCrs().authid()
        self.dumLayer = QgsVectorLayer(
            f"Point?crs={epsg}", "temporary_points", "memory"
        )
        self.actualPointOrientation.setToGeometry(
            self.rotateTool.rotate(
                tmpGeom, self.actualPointDx, angle), self.dumLayer
        )

    def setPosition(self):
        """ Establecer la posición RubberBand """

        # Punto de transformación
        originalPoint = self.selected_features.geometry().asPoint()
        self.actualPointDx = qgsutils.convertProjection(
            originalPoint.x(),
            originalPoint.y(),
            "EPSG:3857",
            self.canvas.mapSettings().destinationCrs().authid(),
        )

        self.positionDx = QgsRubberBand(
            self.iface.mapCanvas(), QgsWkbTypes.PointGeometry)
        self.positionDx.setWidth(3)
        self.positionDx.setIcon(QgsRubberBand.ICON_BOX)
        self.positionDx.setIconSize(3)
        self.positionDx.setColor(Qt.blue)
        self.positionSx = QgsRubberBand(
            self.iface.mapCanvas(), QgsWkbTypes.PointGeometry
        )
        self.positionSx.setWidth(3)
        self.positionSx.setIcon(QgsRubberBand.ICON_BOX)
        self.positionSx.setIconSize(3)
        self.positionSx.setColor(Qt.blue)
        self.positionInt = QgsRubberBand(
            self.iface.mapCanvas(), QgsWkbTypes.PointGeometry
        )
        self.positionInt.setWidth(6)
        self.positionInt.setIcon(QgsRubberBand.ICON_BOX)
        self.positionInt.setIconSize(3)
        self.positionInt.setColor(Qt.blue)

        self.positionDx.addPoint(self.actualPointDx)
        self.positionSx.addPoint(self.actualPointDx)
        self.positionInt.addPoint(self.actualPointDx)

    def closeEvent(self, _):
        """ Cerrar cuadro de diálogo """
        self.resetQgsRubberBand()
        self.canvas.refresh()
        self.iface.actionPan().trigger()
        self.parent.orbitalViewer = None
        self.RemoveImage()

    def resetQgsRubberBand(self):
        """ Retire RubberBand """
        try:
            self.positionSx.reset()
            self.positionInt.reset()
            self.positionDx.reset()
            self.actualPointOrientation.reset()
        except Exception:
            None