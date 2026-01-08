# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CSVGeometryImportPlugin
                                 A QGIS plugin
 Import CSV files with various geometry formats (WKT, WKB, GeoJSON, KML, etc.)
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
 This script initializes the plugin, making it known to QGIS.
"""

def classFactory(iface):
    """Load CSVGeometryImportPlugin class from file main_plugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .main_plugin import CSVGeometryImportPlugin
    return CSVGeometryImportPlugin(iface)
