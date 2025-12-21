# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CSVGeometryImportDialog
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
import csv
import codecs
from typing import List, Dict, Optional, Tuple

from PyQt5.QtCore import Qt, QSettings, QVariant
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QGroupBox, QComboBox, QCheckBox, QProgressBar, QFrame,
    QSizePolicy, QSpacerItem, QWidget
)

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry,
    QgsCoordinateReferenceSystem, QgsWkbTypes, QgsMessageLog, Qgis,
    QgsCoordinateTransform
)
from qgis.gui import QgsProjectionSelectionWidget

from .geometry_parsers import GeometryParser, GeometryFormat


class CSVGeometryImportDialog(QDialog):
    """Dialog for importing CSV files with various geometry formats"""
    
    # Delimiter options
    DELIMITER_OPTIONS = {
        'Comma (,)': ',',
        'Semicolon (;)': ';',
        'Tab': '\t',
        'Pipe (|)': '|',
        'Space': ' '
    }
    
    def __init__(self, parent=None):
        """Initialize the dialog"""
        super().__init__(parent)
        
        self.csv_path = None
        self.csv_headers = []
        self.csv_preview_data = []
        self.detected_format = GeometryFormat.UNKNOWN
        
        self.setup_ui()
        self.load_settings()
        self.connect_signals()
    
    def get_all_available_encodings(self) -> List[str]:
        """Get list of common encodings"""
        return [
            'UTF-8', 'UTF-16', 'UTF-32',
            'ASCII', 'ISO-8859-1', 'ISO-8859-2', 'ISO-8859-15',
            'Windows-1250', 'Windows-1251', 'Windows-1252', 'Windows-1256',
            'CP437', 'CP850', 'CP866', 'CP1252',
            'Latin-1', 'Latin-2',
            'KOI8-R', 'KOI8-U',
            'GB2312', 'GBK', 'GB18030',
            'Big5', 'Big5-HKSCS',
            'EUC-JP', 'EUC-KR', 'Shift_JIS',
            'UTF-8-SIG'
        ]
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle('Import CSV with Geometry')
        self.setMinimumWidth(700)
        self.setMinimumHeight(650)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # ============ File Selection Group ============
        file_group = QGroupBox('CSV File')
        file_layout = QHBoxLayout(file_group)
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText('Select a CSV file...')
        self.file_path_edit.setReadOnly(True)
        
        self.browse_btn = QPushButton('Browse...')
        self.browse_btn.setFixedWidth(100)
        
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.browse_btn)
        main_layout.addWidget(file_group)
        
        # ============ CSV Options Group ============
        csv_options_group = QGroupBox('CSV Options')
        csv_options_layout = QGridLayout(csv_options_group)
        
        # Delimiter
        csv_options_layout.addWidget(QLabel('Delimiter:'), 0, 0)
        self.delimiter_combo = QComboBox()
        self.delimiter_combo.addItems(list(self.DELIMITER_OPTIONS.keys()))
        csv_options_layout.addWidget(self.delimiter_combo, 0, 1)
        
        # Encoding
        csv_options_layout.addWidget(QLabel('Encoding:'), 0, 2)
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(self.get_all_available_encodings())
        self.encoding_combo.setCurrentText('UTF-8')
        csv_options_layout.addWidget(self.encoding_combo, 0, 3)
        
        # Has header checkbox
        self.has_header_check = QCheckBox('First row contains column names')
        self.has_header_check.setChecked(True)
        csv_options_layout.addWidget(self.has_header_check, 1, 0, 1, 2)
        
        # Reload button
        self.reload_btn = QPushButton('Reload CSV')
        self.reload_btn.setFixedWidth(100)
        self.reload_btn.setEnabled(False)
        csv_options_layout.addWidget(self.reload_btn, 1, 3)
        
        main_layout.addWidget(csv_options_group)
        
        # ============ Geometry Options Group ============
        geom_group = QGroupBox('Geometry Options')
        geom_layout = QGridLayout(geom_group)
        
        # Geometry format
        geom_layout.addWidget(QLabel('Geometry Format:'), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItem('Auto-detect')
        self.format_combo.addItems(GeometryFormat.all_formats())
        geom_layout.addWidget(self.format_combo, 0, 1)
        
        # Detected format label
        self.detected_format_label = QLabel('')
        self.detected_format_label.setStyleSheet('color: #666; font-style: italic;')
        geom_layout.addWidget(self.detected_format_label, 0, 2, 1, 2)
        
        # Geometry column
        self.geom_column_label = QLabel('Geometry Column:')
        geom_layout.addWidget(self.geom_column_label, 1, 0)
        self.geom_column_combo = QComboBox()
        self.geom_column_combo.setMinimumWidth(200)
        geom_layout.addWidget(self.geom_column_combo, 1, 1)
        
        # X column (for X-Y format)
        self.x_column_label = QLabel('X (Longitude) Column:')
        geom_layout.addWidget(self.x_column_label, 2, 0)
        self.x_column_combo = QComboBox()
        geom_layout.addWidget(self.x_column_combo, 2, 1)
        
        # Y column (for X-Y format)
        self.y_column_label = QLabel('Y (Latitude) Column:')
        geom_layout.addWidget(self.y_column_label, 2, 2)
        self.y_column_combo = QComboBox()
        geom_layout.addWidget(self.y_column_combo, 2, 3)
        
        # Initially hide X-Y options
        self.toggle_xy_options(False)
        
        main_layout.addWidget(geom_group)
        
        # ============ CRS Options Group ============
        crs_group = QGroupBox('Coordinate Reference System (CRS)')
        crs_layout = QGridLayout(crs_group)
        
        crs_layout.addWidget(QLabel('Source CRS:'), 0, 0)
        self.crs_selector = QgsProjectionSelectionWidget()
        self.crs_selector.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
        self.crs_selector.setOptionVisible(QgsProjectionSelectionWidget.LayerCrs, False)
        self.crs_selector.setOptionVisible(QgsProjectionSelectionWidget.ProjectCrs, True)
        self.crs_selector.setOptionVisible(QgsProjectionSelectionWidget.CurrentCrs, True)
        self.crs_selector.setOptionVisible(QgsProjectionSelectionWidget.DefaultCrs, True)
        self.crs_selector.setOptionVisible(QgsProjectionSelectionWidget.RecentCrs, True)
        crs_layout.addWidget(self.crs_selector, 0, 1, 1, 3)
        
        # CRS info label
        self.crs_info_label = QLabel('Default: EPSG:4326 (WGS 84)')
        self.crs_info_label.setStyleSheet('color: #666; font-style: italic;')
        crs_layout.addWidget(self.crs_info_label, 1, 0, 1, 4)
        
        main_layout.addWidget(crs_group)
        
        # ============ Layer Options Group ============
        layer_group = QGroupBox('Layer Options')
        layer_layout = QGridLayout(layer_group)
        
        # Layer name
        layer_layout.addWidget(QLabel('Layer Name:'), 0, 0)
        self.layer_name_edit = QLineEdit()
        self.layer_name_edit.setPlaceholderText('Enter layer name (default: CSV filename)')
        layer_layout.addWidget(self.layer_name_edit, 0, 1, 1, 3)
        
        # Add to map checkbox
        self.add_to_map_check = QCheckBox('Add layer to map after import')
        self.add_to_map_check.setChecked(True)
        layer_layout.addWidget(self.add_to_map_check, 1, 0, 1, 2)
        
        # Skip invalid geometries
        self.skip_invalid_check = QCheckBox('Skip rows with invalid geometries')
        self.skip_invalid_check.setChecked(True)
        layer_layout.addWidget(self.skip_invalid_check, 1, 2, 1, 2)
        
        main_layout.addWidget(layer_group)
        
        # ============ Preview Group ============
        preview_group = QGroupBox('CSV Preview (first 10 rows)')
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.preview_table.setMinimumHeight(150)
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        preview_layout.addWidget(self.preview_table)
        
        # Row count label
        self.row_count_label = QLabel('')
        self.row_count_label.setStyleSheet('color: #666;')
        preview_layout.addWidget(self.row_count_label)
        
        main_layout.addWidget(preview_group)
        
        # ============ Progress Bar ============
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # ============ Buttons ============
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.import_btn = QPushButton('Import')
        self.import_btn.setFixedWidth(100)
        self.import_btn.setEnabled(False)
        self.import_btn.setDefault(True)
        
        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.setFixedWidth(100)
        
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(button_layout)
    
    def connect_signals(self):
        """Connect UI signals to slots"""
        self.browse_btn.clicked.connect(self.browse_file)
        self.reload_btn.clicked.connect(self.reload_csv)
        self.delimiter_combo.currentIndexChanged.connect(self.on_csv_options_changed)
        self.encoding_combo.currentIndexChanged.connect(self.on_csv_options_changed)
        self.has_header_check.stateChanged.connect(self.on_csv_options_changed)
        self.format_combo.currentIndexChanged.connect(self.on_format_changed)
        self.geom_column_combo.currentIndexChanged.connect(self.on_geom_column_changed)
        self.crs_selector.crsChanged.connect(self.on_crs_changed)
        self.import_btn.clicked.connect(self.import_csv)
        self.cancel_btn.clicked.connect(self.reject)
    
    def toggle_xy_options(self, show: bool):
        """Show or hide X-Y coordinate options"""
        self.x_column_label.setVisible(show)
        self.x_column_combo.setVisible(show)
        self.y_column_label.setVisible(show)
        self.y_column_combo.setVisible(show)
        
        # Hide geometry column for X-Y mode
        self.geom_column_label.setVisible(not show)
        self.geom_column_combo.setVisible(not show)
    
    def browse_file(self):
        """Open file browser to select CSV file"""
        settings = QSettings()
        last_dir = settings.value('CSVGeometryImport/lastDirectory', '')
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Select CSV File',
            last_dir,
            'CSV Files (*.csv *.txt);;All Files (*.*)'
        )
        
        if file_path:
            settings.setValue('CSVGeometryImport/lastDirectory', os.path.dirname(file_path))
            self.csv_path = file_path
            self.file_path_edit.setText(file_path)
            self.reload_btn.setEnabled(True)
            
            # Set default layer name from filename
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            self.layer_name_edit.setText(base_name)
            
            # Load and preview CSV
            self.load_csv()
    
    def on_csv_options_changed(self):
        """Handle changes to CSV parsing options"""
        if self.csv_path:
            self.load_csv()
    
    def reload_csv(self):
        """Reload the CSV file with current options"""
        if self.csv_path:
            self.load_csv()
    
    def get_selected_delimiter(self) -> str:
        """Get the currently selected delimiter character"""
        delimiter_name = self.delimiter_combo.currentText()
        return self.DELIMITER_OPTIONS.get(delimiter_name, ',')
    
    def get_selected_encoding(self) -> str:
        """Get the currently selected encoding"""
        return self.encoding_combo.currentText()
    
    def load_csv(self):
        """Load and preview the CSV file"""
        if not self.csv_path or not os.path.exists(self.csv_path):
            return
        
        try:
            delimiter = self.get_selected_delimiter()
            encoding = self.get_selected_encoding()
            has_header = self.has_header_check.isChecked()
            
            with codecs.open(self.csv_path, 'r', encoding=encoding, errors='replace') as f:
                # Use csv.Sniffer to detect if needed
                reader = csv.reader(f, delimiter=delimiter)
                
                rows = list(reader)
                
                if not rows:
                    QMessageBox.warning(self, 'Warning', 'The CSV file is empty.')
                    return
                
                # Get headers
                if has_header:
                    self.csv_headers = rows[0]
                    data_rows = rows[1:]
                else:
                    # Generate column names
                    self.csv_headers = [f'Column_{i+1}' for i in range(len(rows[0]))]
                    data_rows = rows
                
                # Store preview data (first 10 rows)
                self.csv_preview_data = data_rows[:10]
                total_rows = len(data_rows)
                
                # Update row count label
                self.row_count_label.setText(f'Total rows: {total_rows:,}')
                
                # Update preview table
                self.update_preview_table()
                
                # Update column dropdowns
                self.update_column_combos()
                
                # Enable import button
                self.import_btn.setEnabled(True)
                
        except Exception as e:
            QMessageBox.critical(
                self, 'Error',
                f'Failed to read CSV file:\n{str(e)}'
            )
            QgsMessageLog.logMessage(
                f"Error reading CSV: {str(e)}",
                'CSV Geometry Import', Qgis.Critical
            )
    
    def update_preview_table(self):
        """Update the preview table with CSV data"""
        self.preview_table.clear()
        
        if not self.csv_headers:
            return
        
        # Set up table
        self.preview_table.setColumnCount(len(self.csv_headers))
        self.preview_table.setHorizontalHeaderLabels(self.csv_headers)
        self.preview_table.setRowCount(len(self.csv_preview_data))
        
        # Populate data
        for row_idx, row in enumerate(self.csv_preview_data):
            for col_idx, value in enumerate(row):
                if col_idx < len(self.csv_headers):
                    item = QTableWidgetItem(str(value)[:100])  # Truncate long values
                    self.preview_table.setItem(row_idx, col_idx, item)
        
        # Resize columns to content
        self.preview_table.resizeColumnsToContents()
    
    def update_column_combos(self):
        """Update column selection dropdowns"""
        # Store current selections
        current_geom = self.geom_column_combo.currentText()
        current_x = self.x_column_combo.currentText()
        current_y = self.y_column_combo.currentText()
        
        # Clear and populate
        self.geom_column_combo.clear()
        self.x_column_combo.clear()
        self.y_column_combo.clear()
        
        self.geom_column_combo.addItems(self.csv_headers)
        self.x_column_combo.addItems(self.csv_headers)
        self.y_column_combo.addItems(self.csv_headers)
        
        # Try to restore selections or auto-detect
        if current_geom and current_geom in self.csv_headers:
            self.geom_column_combo.setCurrentText(current_geom)
        else:
            self.auto_detect_geometry_column()
        
        if current_x and current_x in self.csv_headers:
            self.x_column_combo.setCurrentText(current_x)
        else:
            self.auto_detect_xy_columns()
        
        if current_y and current_y in self.csv_headers:
            self.y_column_combo.setCurrentText(current_y)
    
    def auto_detect_geometry_column(self):
        """Try to auto-detect the geometry column"""
        geometry_keywords = [
            'geometry', 'geom', 'wkt', 'wkb', 'shape', 'the_geom',
            'geojson', 'geo_json', 'coordinates', 'coord'
        ]
        
        for col in self.csv_headers:
            if col.lower() in geometry_keywords or any(kw in col.lower() for kw in geometry_keywords):
                self.geom_column_combo.setCurrentText(col)
                self.detect_geometry_format()
                return
        
        # If no geometry column found, try to detect from content
        if self.csv_preview_data and self.csv_headers:
            for col_idx, col in enumerate(self.csv_headers):
                if col_idx < len(self.csv_preview_data[0]):
                    sample = self.csv_preview_data[0][col_idx]
                    detected = GeometryParser.detect_format(sample)
                    if detected != GeometryFormat.UNKNOWN:
                        self.geom_column_combo.setCurrentText(col)
                        self.detected_format = detected
                        self.detected_format_label.setText(f'(Detected: {detected})')
                        return
    
    def auto_detect_xy_columns(self):
        """Try to auto-detect X and Y columns"""
        x_keywords = ['lon', 'longitude', 'lng', 'x', 'long', 'x_coord', 'xcoord', 'easting']
        y_keywords = ['lat', 'latitude', 'y', 'y_coord', 'ycoord', 'northing']
        
        for col in self.csv_headers:
            col_lower = col.lower()
            if any(kw == col_lower or kw in col_lower for kw in x_keywords):
                self.x_column_combo.setCurrentText(col)
            if any(kw == col_lower or kw in col_lower for kw in y_keywords):
                self.y_column_combo.setCurrentText(col)
    
    def on_format_changed(self):
        """Handle geometry format selection change"""
        format_text = self.format_combo.currentText()
        
        # Show/hide X-Y options
        is_xy = format_text == GeometryFormat.XY
        self.toggle_xy_options(is_xy)
        
        # Clear detected format label if manual selection
        if format_text != 'Auto-detect':
            self.detected_format_label.setText('')
    
    def on_geom_column_changed(self):
        """Handle geometry column selection change"""
        if self.format_combo.currentText() == 'Auto-detect':
            self.detect_geometry_format()
    
    def detect_geometry_format(self):
        """Detect geometry format from selected column"""
        col_name = self.geom_column_combo.currentText()
        
        if not col_name or col_name not in self.csv_headers:
            return
        
        col_idx = self.csv_headers.index(col_name)
        
        # Try to detect from first non-empty sample
        for row in self.csv_preview_data:
            if col_idx < len(row) and row[col_idx]:
                sample = row[col_idx]
                detected = GeometryParser.detect_format(sample)
                if detected != GeometryFormat.UNKNOWN:
                    self.detected_format = detected
                    self.detected_format_label.setText(f'(Detected: {detected})')
                    return
        
        self.detected_format = GeometryFormat.UNKNOWN
        self.detected_format_label.setText('(Could not detect format)')
    
    def on_crs_changed(self):
        """Handle CRS selection change"""
        crs = self.crs_selector.crs()
        if crs.isValid():
            self.crs_info_label.setText(f'Selected: {crs.authid()} ({crs.description()})')
        else:
            self.crs_info_label.setText('Invalid CRS selected')
    
    def get_format_to_use(self) -> str:
        """Get the geometry format to use for parsing"""
        format_text = self.format_combo.currentText()
        
        if format_text == 'Auto-detect':
            return self.detected_format
        return format_text
    
    def import_csv(self):
        """Import the CSV file as a QGIS layer"""
        if not self.csv_path:
            QMessageBox.warning(self, 'Warning', 'Please select a CSV file first.')
            return
        
        format_type = self.get_format_to_use()
        
        if format_type == GeometryFormat.UNKNOWN:
            QMessageBox.warning(
                self, 'Warning',
                'Could not detect geometry format. Please select a format manually.'
            )
            return
        
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.import_btn.setEnabled(False)
            
            # Get options
            delimiter = self.get_selected_delimiter()
            encoding = self.get_selected_encoding()
            has_header = self.has_header_check.isChecked()
            skip_invalid = self.skip_invalid_check.isChecked()
            layer_name = self.layer_name_edit.text() or os.path.splitext(
                os.path.basename(self.csv_path)
            )[0]
            
            # Get CRS
            crs = self.crs_selector.crs()
            if not crs.isValid():
                crs = QgsCoordinateReferenceSystem('EPSG:4326')
            
            # Read all data
            with codecs.open(self.csv_path, 'r', encoding=encoding, errors='replace') as f:
                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)
            
            if not rows:
                QMessageBox.warning(self, 'Warning', 'The CSV file is empty.')
                return
            
            # Get headers and data
            if has_header:
                headers = rows[0]
                data_rows = rows[1:]
            else:
                headers = [f'Column_{i+1}' for i in range(len(rows[0]))]
                data_rows = rows
            
            total_rows = len(data_rows)
            self.progress_bar.setMaximum(total_rows)
            
            # Determine geometry column index
            if format_type == GeometryFormat.XY:
                x_col = self.x_column_combo.currentText()
                y_col = self.y_column_combo.currentText()
                x_idx = headers.index(x_col) if x_col in headers else -1
                y_idx = headers.index(y_col) if y_col in headers else -1
                
                if x_idx < 0 or y_idx < 0:
                    QMessageBox.warning(self, 'Warning', 'Please select valid X and Y columns.')
                    return
                
                geom_col_idx = -1
                attribute_headers = [h for i, h in enumerate(headers) if i not in (x_idx, y_idx)]
            else:
                geom_col = self.geom_column_combo.currentText()
                if geom_col not in headers:
                    QMessageBox.warning(self, 'Warning', 'Please select a valid geometry column.')
                    return
                
                geom_col_idx = headers.index(geom_col)
                x_idx = y_idx = -1
                attribute_headers = [h for i, h in enumerate(headers) if i != geom_col_idx]
            
            # Determine geometry type from first valid geometry
            geom_type = QgsWkbTypes.Unknown
            for row in data_rows[:100]:  # Check first 100 rows
                if format_type == GeometryFormat.XY:
                    geom_type = QgsWkbTypes.Point
                    break
                else:
                    if geom_col_idx < len(row) and row[geom_col_idx]:
                        geom = GeometryParser.parse(row[geom_col_idx], format_type)
                        if geom and not geom.isNull():
                            geom_type = geom.wkbType()
                            break
            
            # Create memory layer
            geom_type_str = QgsWkbTypes.displayString(geom_type) if geom_type != QgsWkbTypes.Unknown else 'Point'
            layer = QgsVectorLayer(
                f'{geom_type_str}?crs={crs.authid()}',
                layer_name,
                'memory'
            )
            
            if not layer.isValid():
                QMessageBox.critical(self, 'Error', 'Failed to create memory layer.')
                return
            
            provider = layer.dataProvider()
            
            # Add attribute fields
            fields = [QgsField(name, QVariant.String) for name in attribute_headers]
            provider.addAttributes(fields)
            layer.updateFields()
            
            # Add features
            features = []
            invalid_count = 0
            
            for row_idx, row in enumerate(data_rows):
                if row_idx % 100 == 0:
                    self.progress_bar.setValue(row_idx)
                    QCoreApplication.processEvents()
                
                # Parse geometry
                if format_type == GeometryFormat.XY:
                    try:
                        x_val = float(row[x_idx]) if x_idx < len(row) else None
                        y_val = float(row[y_idx]) if y_idx < len(row) else None
                        geom = GeometryParser.parse('', format_type, x_value=x_val, y_value=y_val)
                    except (ValueError, IndexError):
                        geom = None
                else:
                    geom_value = row[geom_col_idx] if geom_col_idx < len(row) else ''
                    geom = GeometryParser.parse(geom_value, format_type)
                
                if geom is None or geom.isNull():
                    invalid_count += 1
                    if skip_invalid:
                        continue
                    else:
                        geom = QgsGeometry()  # Empty geometry
                
                # Create feature
                feat = QgsFeature()
                feat.setGeometry(geom)
                
                # Set attributes (excluding geometry column)
                attrs = []
                for i, h in enumerate(headers):
                    if format_type == GeometryFormat.XY:
                        if i not in (x_idx, y_idx):
                            attrs.append(row[i] if i < len(row) else '')
                    else:
                        if i != geom_col_idx:
                            attrs.append(row[i] if i < len(row) else '')
                
                feat.setAttributes(attrs)
                features.append(feat)
            
            # Add all features
            provider.addFeatures(features)
            layer.updateExtents()
            
            self.progress_bar.setValue(total_rows)
            
            # Add to map if requested
            if self.add_to_map_check.isChecked():
                QgsProject.instance().addMapLayer(layer)
            
            # Show success message
            success_msg = f'Successfully imported {len(features):,} features.'
            if invalid_count > 0:
                success_msg += f'\n{invalid_count:,} rows had invalid geometries'
                if skip_invalid:
                    success_msg += ' and were skipped.'
                else:
                    success_msg += ' (imported with empty geometry).'
            
            QMessageBox.information(self, 'Success', success_msg)
            
            # Save settings
            self.save_settings()
            
            # Accept dialog
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self, 'Error',
                f'Failed to import CSV:\n{str(e)}'
            )
            QgsMessageLog.logMessage(
                f"Import error: {str(e)}",
                'CSV Geometry Import', Qgis.Critical
            )
        finally:
            self.progress_bar.setVisible(False)
            self.import_btn.setEnabled(True)
    
    def load_settings(self):
        """Load saved settings"""
        settings = QSettings()
        
        # Delimiter
        delimiter = settings.value('CSVGeometryImport/delimiter', 'Comma (,)')
        idx = self.delimiter_combo.findText(delimiter)
        if idx >= 0:
            self.delimiter_combo.setCurrentIndex(idx)
        
        # Encoding
        encoding = settings.value('CSVGeometryImport/encoding', 'UTF-8')
        idx = self.encoding_combo.findText(encoding)
        if idx >= 0:
            self.encoding_combo.setCurrentIndex(idx)
        
        # CRS
        crs_auth = settings.value('CSVGeometryImport/crs', 'EPSG:4326')
        self.crs_selector.setCrs(QgsCoordinateReferenceSystem(crs_auth))
        
        # Options
        self.has_header_check.setChecked(
            settings.value('CSVGeometryImport/hasHeader', True, type=bool)
        )
        self.add_to_map_check.setChecked(
            settings.value('CSVGeometryImport/addToMap', True, type=bool)
        )
        self.skip_invalid_check.setChecked(
            settings.value('CSVGeometryImport/skipInvalid', True, type=bool)
        )
    
    def save_settings(self):
        """Save current settings"""
        settings = QSettings()
        
        settings.setValue('CSVGeometryImport/delimiter', self.delimiter_combo.currentText())
        settings.setValue('CSVGeometryImport/encoding', self.encoding_combo.currentText())
        settings.setValue('CSVGeometryImport/crs', self.crs_selector.crs().authid())
        settings.setValue('CSVGeometryImport/hasHeader', self.has_header_check.isChecked())
        settings.setValue('CSVGeometryImport/addToMap', self.add_to_map_check.isChecked())
        settings.setValue('CSVGeometryImport/skipInvalid', self.skip_invalid_check.isChecked())


# Import QCoreApplication for processEvents
from PyQt5.QtCore import QCoreApplication
