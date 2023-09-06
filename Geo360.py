import time
import os

from qgis.gui import QgsMapToolIdentify
from qgis.PyQt.QtCore import Qt, QSettings, QThread
from qgis.PyQt.QtGui import QIcon, QCursor, QPixmap
from qgis.PyQt.QtWidgets import QAction
from .Geo360Dialog import Geo360Dialog
from . import config
from .utils.log import log
from .utils.qgsutils import qgsutils
from qgis.core import(
    QgsApplication,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsPointXY)
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

class Geo360:
    def __init__(self, iface):
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        threadcount = QThread.idealThreadCount()
        QgsApplication.setMaxThreads(threadcount)
        QSettings().setValue("/qgis/parallel_rendering", True)
        QSettings().setValue("/core/OpenClEnabled", True)
        self.orbitalViewer = None
        self.server = None
        self.make_server()

    def initGui(self):
        log.initLogging()
        self.action = QAction(
            QIcon(":/Visor360/images/icon"),
            u"Visor 360°",
            self.iface.mainWindow(),
        )
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&Visor 360°", self.action)

    def unload(self):
        self.iface.removePluginMenu(u"&Visor 360°", self.action)
        self.iface.removeToolBarIcon(self.action)
        self.close_server()

    def close_server(self):
        if self.server is not None:
            self.server.shutdown()
            time.sleep(1)
            self.server.server_close()
            while self.server_thread.is_alive():
                self.server_thread.join()
            self.server = None

    def make_server(self):
        self.close_server()
        directory = (
            QgsApplication.qgisSettingsDirPath().replace("\\", "/")
            + "python/plugins/Visor360/viewer"
        )
        try:
            self.server = ThreadingHTTPServer(
                (config.IP, config.PORT),
                partial(QuietHandler, directory=directory),
            )
            self.server_thread = Thread(
                target=self.server.serve_forever, name="http_server"
            )
            self.server_thread.daemon = True
            print("Serving on port: %s" % self.server.server_address[1])
            time.sleep(1)
            self.server_thread.start()
        except Exception:
            print("Server Error")

    def run(self):
        self.found = False
        lys = self.canvas.layers()
        for layer in lys:
            layer.name() == config.layer_name
            self.found = True
            self.mapTool = SelectTool(self.iface, parent=self, layer=layer)
            self.iface.mapCanvas().setMapTool(self.mapTool)

        # if not self.found:
        #     qgsutils.showUserAndLogMessage(
        #         u"Información: ", u"Necesitas subir recorrido."
        #     )
            # return

    def ShowViewer(self, x, y):
        """ Mostrar el visor de imágenes 360° """
        self.orbitalViewer = Geo360Dialog(self.iface, self, x, y)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.orbitalViewer)
        self.orbitalViewer.show()


    # def ShowViewer(self, x=None, y=None):
    #     self.x = x
    #     self.y = y

    #     if self.orbitalViewer is None:
    #         self.orbitalViewer = Geo360Dialog(
    #             self.iface, parent=self, x=x, y=y
    #         )
    #         # self.orbitalViewer = Geo360Dialog(self.iface, self.layer, x, y)
    #         self.iface.addDockWidget(Qt.RightDockWidgetArea, self.orbitalViewer)
    #     else:
    #         self.orbitalViewer.ReloadView(self.x, self.y)

class SelectTool(QgsMapToolIdentify):
    def __init__(self, iface, parent=None, layer=None):
        QgsMapToolIdentify.__init__(self, iface.mapCanvas())
        self.canvas = iface.mapCanvas()
        self.iface = iface
        self.layer = layer
        self.parent = parent

        project_root = os.path.dirname(__file__)
        
        image_filename = "cursorIcon.png"
        image_path = os.path.join(project_root, image_filename)

        cursor_image = QPixmap(image_path)
        self.custom_cursor = QCursor(cursor_image)

    def activate(self):
        self.canvas.setCursor(self.custom_cursor)

    def canvasReleaseEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()

        point = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)
        self.parent.ShowViewer(
            x=point[0],
            y=point[1],
        )