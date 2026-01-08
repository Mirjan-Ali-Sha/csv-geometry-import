# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CSVGeometryImportPlugin
                                 A QGIS plugin
 Import CSV files with various geometry formats
                              -------------------
        begin                : 2025-12-21
        copyright            : (C) 2025 by Mirjan Ali Sha
        email                : mastools.help@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from PyQt5.QtCore import QCoreApplication, QSettings, QTranslator
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMessageBox, QToolBar

from qgis.core import QgsMessageLog, Qgis


class CSVGeometryImportPlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        
        # Initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        
        # Initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            f'CSVGeometryImport_{locale}.qm'
        )
        
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        
        # Menu and toolbar identifiers - matching csv_geometry_export pattern
        self.menu = self.tr('&MAS Vector Processing')
        self.toolbar = None
        self.actions = []
        self.plugin_action = None
        
        # Plugin dialog
        self.dlg = None

    def tr(self, message):
        """Get the translation for a string using Qt translation API."""
        return QCoreApplication.translate('CSVGeometryImport', message)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        
        # Check if the MAS Vector Processing toolbar already exists; if not, create it
        self.toolbar = self.iface.mainWindow().findChild(QToolBar, 'MASVectorProcessingToolbar')
        if self.toolbar is None:
            self.toolbar = self.iface.addToolBar(self.tr('MAS Vector Processing'))
            self.toolbar.setObjectName('MASVectorProcessingToolbar')
        
        # Create icon path
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        if not os.path.exists(icon_path):
            # Create a default icon if missing
            self.create_default_icon(icon_path)
        
        # Create main action
        self.plugin_action = QAction(
            QIcon(icon_path),
            self.tr('Import CSV with Geometry'),
            self.iface.mainWindow()
        )
        self.plugin_action.triggered.connect(self.run)
        self.plugin_action.setStatusTip(self.tr('Import CSV files with various geometry formats'))
        self.plugin_action.setWhatsThis(self.tr(
            'Import CSV files containing geometry data in formats like '
            'WKT, WKB, GeoJSON, KML, Earth Engine, TopoJSON, or X-Y coordinates'
        ))
        self.plugin_action.setEnabled(True)
        
        # Add the action under the "MAS Vector Processing" entry of the Vector menu
        self.iface.addPluginToVectorMenu(self.menu, self.plugin_action)
        
        # Add the action to the toolbar
        self.toolbar.addAction(self.plugin_action)
        
        # Store action
        self.actions.append(self.plugin_action)

    def create_default_icon(self, icon_path):
        """Create a default icon if none exists with blue color #323FFF"""
        try:
            from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush
            from PyQt5.QtCore import Qt
            
            # Create 24x24 pixel icon (matching csv_geometry_export)
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Use blue color #323FFF (same as csv_geometry_export)
            blue_color = QColor("#323FFF")
            
            # Draw background with blue color
            painter.setBrush(QBrush(blue_color))
            painter.setPen(QPen(blue_color, 1))
            painter.drawRoundedRect(2, 2, 20, 20, 3, 3)
            
            # Draw CSV text in white for good contrast
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(QFont("Arial", 7, QFont.Bold))
            painter.drawText(4, 15, "CSV")
            
            painter.end()
            pixmap.save(icon_path)
            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Could not create default icon: {str(e)}",
                'CSV Geometry Import', Qgis.Warning
            )

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        # Remove actions from menu
        for action in self.actions:
            self.iface.removePluginVectorMenu(self.menu, action)
        
        # Toolbar cleanup - QGIS will remove the toolbar if no actions remain
        if self.toolbar:
            self.toolbar = None
        
        # Clear actions list
        self.actions = []

    def run(self):
        """Run method that performs all the real work"""
        try:
            from .import_dialog import CSVGeometryImportDialog
            
            # Create and show the dialog
            self.dlg = CSVGeometryImportDialog(parent=self.iface.mainWindow())
            
            # Show the dialog
            result = self.dlg.exec_()
            
            if result:
                QgsMessageLog.logMessage(
                    "CSV import completed successfully",
                    'CSV Geometry Import', Qgis.Info
                )
                
        except Exception as e:
            QMessageBox.critical(
                self.iface.mainWindow(),
                self.tr('Error'),
                self.tr(f'An error occurred: {str(e)}')
            )
            QgsMessageLog.logMessage(
                f"Error in CSV Geometry Import: {str(e)}",
                'CSV Geometry Import', Qgis.Critical
            )
