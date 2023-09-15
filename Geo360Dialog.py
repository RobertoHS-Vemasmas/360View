import math
import os

from qgis.PyQt.QtWidgets import QDialog, QWidget, QDockWidget
from qgis.PyQt.QtGui import QWindow
from . import config
from .geom.transformgeom import transformGeometry
from .ui.output_ui  import Ui_orbitalDialog
from .utils.qgsutils import qgsutils
from qgis.PyQt.QtWebKitWidgets import QWebView, QWebPage
from qgis.PyQt.QtWebKit import QWebSettings
from qgis.gui import QgsRubberBand
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager
from qgis.core import(
    QgsPointXY, 
    QgsProject, 
    QgsFeatureRequest,
    QgsVectorLayer, 
    QgsWkbTypes)

from qgis.PyQt.QtCore import (
    Qt,
    pyqtSignal,
    QUrl,
    QJsonDocument,
    QObject,
    QByteArray)

from qgis.PyQt.QtNetwork import(
    QNetworkRequest,
    QNetworkAccessManager,
    QNetworkRequest,
    QNetworkAccessManager,
    QNetworkReply,
    QSslSocket)


class _ViewerPage(QWebPage):
    obj = []  # Sincrónico
    newData = pyqtSignal(list) # Asincrónico

    def javaScriptConsoleMessage(self, msg, line, source):
        l = msg.split(",")
        self.obj = l
        self.newData.emit(l)

class Geo360Dialog(QDockWidget, Ui_orbitalDialog):

    """Geo360 Dialog Class"""

    def __init__(self, iface, parent=None, x=None, y=None, layer=None):

        QDockWidget.__init__(self)

        self.setupUi(self)

        self.DEFAULT_URL = (f"http://{config.IP}:{str(config.PORT)}/viewer.html")
        self.DEFAULT_EMPTY = (f"http://{config.IP}:{str(config.PORT)}/none.html")
        self.DEFAULT_BLANK = (f"http://{config.IP}:{str(config.PORT)}/blank.html")


        # Crear vista
        

        self.plugin_path = os.path.dirname(os.path.realpath(__file__))
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.parent = parent
        self.selected_features = None

        self.x = x
        self.y = y
        self.found = False
        self.actualPointOrientation = None
        self.RemoveImage()

        
        # Obtener la ruta de la imagen.
        self.current_image = None
        self.imagenesRecorrido = []
        self.currentIndex = 0
        self.GetImage()

      

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
        self.cef_widget.setPage(self.page)

        self.cef_widget.load(QUrl(self.DEFAULT_URL))
        self.ViewerLayout.addWidget(self.cef_widget, 1, 0)


    def GetImage(self):
        """ Obtener la imagen seleccionada """
        self.x = round(self.x, 5)
        self.y = round(self.y, 5)
        json = {'latitud' : self.y, 'longitud' : self.x} # Se invierten las coordenadas
        document = QJsonDocument(json) 

        req = QNetworkRequest(QUrl('https://10.16.106.74/ideeqro_api/recorridos360/existenRecorridos'))
        # req = QNetworkRequest(QUrl('http://localhost:8000/recorridos360/existenRecorridos'))
        req.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, 'application/json')

        conf = req.sslConfiguration()
        conf.setPeerVerifyMode(QSslSocket.VerifyNone)
        req.setSslConfiguration(conf)

        self.nam = QNetworkAccessManager()
        self.nam.finished.connect(self.handleResponse)
        print("Sending request to:", req.url().toString())
        self.nam.post(req, document.toJson())
        print("Request sent")


    def handleResponse(self, reply):
        er = reply.error()
        if er == QNetworkReply.NetworkError.NoError:

            bytes_string = reply.readAll()
            jsonO = QJsonDocument.fromJson(bytes_string)
            cantidad_recorrido = jsonO['cantidadRecorridos'].toInt()

            print("Received response with cantidad_recorrido:", cantidad_recorrido)

            if cantidad_recorrido > 0:
                self.iface.addDockWidget(Qt.RightDockWidgetArea, self)
                self.show()
                self.CreateViewer()
                self.x = round(self.x, 5)
                self.y = round(self.y, 5)
                json = {'latitud' : self.y, 'longitud' : self.x} # Se invierten las coordenadas
                document = QJsonDocument(json)

                req = QNetworkRequest(QUrl('https://10.16.106.74/ideeqro_api/recorridos360/obtenerRecorridos'))
                # req = QNetworkRequest(QUrl('http://localhost:8000/recorridos360/obtenerRecorridos'))
                req.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, 'application/json')

                conf = req.sslConfiguration()
                conf.setPeerVerifyMode(QSslSocket.VerifyNone)
                req.setSslConfiguration(conf)

                self.nam2 = QNetworkAccessManager()
                self.nam2.finished.connect(self.handleRecorrido)
                self.nam2.post(req, document.toJson())

                if cantidad_recorrido == cantidad_recorrido:
                    # Mostrar un mensaje cuando la cantidad de recorridos llega al total
                    qgsutils.showUserAndLogMessage(
                        u"Información:", f"Se han encontrado {cantidad_recorrido} recorridos en total."
                    )
            else:
                qgsutils.showUserAndLogMessage(
                    u"Información:", f"No existen recorridos asociados."
                )
        else:
            error_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            error_url = reply.url().toString()
            error_message = reply.errorString()
    
            qgsutils.showUserAndLogMessage(
                u"Error: ", reply.errorString()
            )

    def handleRecorrido(self, reply):
        er = reply.error()
        if er == QNetworkReply.NetworkError.NoError:
            bytes_string = reply.readAll()
            jsonO = QJsonDocument.fromJson(bytes_string)
            puntos = jsonO['puntos'].toArray()

            for p in puntos:
                imageName = p['imagen'].toString()

                if not imageName.endswith('.jpg'):
                    imageName = imageName + ".jpg"

                imagePath = 'https://10.16.106.74/geo/360/' + p['zona'].toString() + "/" + p['recorrido'].toString() + "/" + imageName,
                
                self.imagenesRecorrido.append(imagePath[0])

            self.current_image = self.imagenesRecorrido[0]

            if self.current_image is not None and isinstance(self.current_image, str):                
                self.DownloadFile(self.current_image)
                self.ChangeUrlViewer(self.DEFAULT_URL)
                
            else:
                qgsutils.showUserAndLogMessage(
                    u"Infornación: ", u"No existe imagen asociada o la ruta es inavlida"
                )
                self.resetQgsRubberBand()
                self.ChangeUrlViewer(self.DEFAULT_EMPTY)
            return
        else:
            error_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            error_url = reply.url().toString()
            error_message = reply.errorString()
  
            qgsutils.showUserAndLogMessage(
                u"Error: ", reply.errorString()
            )

    def DownloadFile(self, src):
        """ Copiar archivo de imagen en servidor local """
        qgsutils.showUserAndLogMessage(
            u"Información: ", u"Copiando imagen", onlyLog=True
        )
        
        req = QNetworkRequest(QUrl(src))

        conf = req.sslConfiguration()
        conf.setPeerVerifyMode(QSslSocket.VerifyNone)
        req.setSslConfiguration(conf)

        self.nam3 = QNetworkAccessManager()
        self.nam3.finished.connect(self.handleDownload)
        self.nam3.get(req)


    def handleDownload(self, reply):
        er = reply.error()

        if er == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            self.saveFile(data)

        else:
            error_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            error_url = reply.url().toString()
            error_message = reply.errorString()
  
            qgsutils.showUserAndLogMessage(
                u"Error: ", reply.errorString()
            )

    def saveFile(self, data):
        dst_dir = self.plugin_path + "/viewer"
        dst_dir = dst_dir + "/image.jpg"

        try:
            os.remove(dst_dir)
        except OSError:
            pass

        f = open(dst_dir, 'wb')
        with f:
            f.write(data)


    def ChangeUrlViewer(self, new_url):
        """Cambiar visor de URL"""
        self.cef_widget.load(QUrl(new_url))


    def GetBackNextImage(self):
        """ Ir a la imagen de atrás """
        sender = QObject.sender(self)

        if sender.objectName() == "btn_next" and self.currentIndex > 0:
            self.currentIndex -= 1
            self.ReloadView()
        elif self.currentIndex < len(self.imagenesRecorrido) - 1:
            self.currentIndex += 1
            self.ReloadView()
        print("URL de la imagen actual:", self.current_image)
        
        #  Actualizar función seleccionada
        # self.ReloadView()


    def ReloadView(self):
        """Recargar visor de imágenes"""
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.RemoveImage()


        #  Activará la ventana
        self.activateWindow()
        # self.showFullScreen()
        self.current_image = self.imagenesRecorrido[self.currentIndex]

        # Comprobar si existe la imagen
        if self.current_image is not None and isinstance(self.current_image, str):
            # Copiar arcivo al servidor local
            self.DownloadFile(self.current_image)
            self.ChangeUrlViewer(self.DEFAULT_URL)

        else:
            qgsutils.showUserAndLogMessage(
                u"Información: ", u"No existe imagen asociada."
            )
            self.ChangeUrlViewer(self.DEFAULT_EMPTY)
            self.resetQgsRubberBand()
            return


    # def FullScreen(self, value):
    #     """ Botón de acción de pantalla completa """
    #     qgsutils.showUserAndLogMessage(
    #         u"Información: ", u"Pantalla completa.", onlyLog=True
    #     )
    #     if value:
    #         self.showFullScreen()
    #     else:
    #         self.showNormal()


    def RemoveImage(self):
        """ Quitar imagen """
        try:
            os.remove(self.plugin_path + "/viewer/image.jpg")
        except OSError:
            pass


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