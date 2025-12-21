# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Geometry Parsers
                                 A QGIS plugin module
 Parse various geometry formats into QgsGeometry objects
                              -------------------
        begin                : 2025-12-21
        copyright            : (C) 2025 by Mirjan Ali Sha
        email                : mastools.help@gmail.com
 ***************************************************************************/
"""

import json
import re
import binascii
from xml.etree import ElementTree as ET
from typing import Optional, Tuple, List, Union

from qgis.core import (
    QgsGeometry, QgsPointXY, QgsWkbTypes, QgsMessageLog, Qgis
)


class GeometryFormat:
    """Enum-like class for geometry format types"""
    WKT = 'WKT'
    WKB = 'WKB'
    EWKT = 'EWKT'
    EWKB = 'EWKB'
    GEOJSON = 'GeoJSON'
    JSON = 'JSON'
    KML = 'KML'
    EARTH_ENGINE = 'Earth Engine'
    TOPOJSON = 'TopoJSON'
    XY = 'X-Y Coordinates'
    UNKNOWN = 'Unknown'
    
    @classmethod
    def all_formats(cls) -> List[str]:
        """Return all supported format names"""
        return [
            cls.WKT, cls.WKB, cls.EWKT, cls.EWKB, 
            cls.GEOJSON, cls.KML, cls.EARTH_ENGINE, 
            cls.TOPOJSON, cls.XY
        ]


class GeometryParser:
    """
    Parse various geometry format strings into QgsGeometry objects.
    
    Supports: WKT, WKB, EWKT, EWKB, GeoJSON, KML, Earth Engine, TopoJSON, X-Y
    """
    
    @staticmethod
    def detect_format(sample: str) -> str:
        """
        Auto-detect geometry format from a sample value.
        
        :param sample: Sample geometry string from CSV
        :return: Detected format name from GeometryFormat
        """
        if not sample or not isinstance(sample, str):
            return GeometryFormat.UNKNOWN
            
        sample = sample.strip()
        
        if not sample:
            return GeometryFormat.UNKNOWN
        
        # EWKT: starts with SRID=
        if sample.upper().startswith('SRID='):
            return GeometryFormat.EWKT
        
        # WKT: starts with geometry type keyword
        wkt_types = [
            'POINT', 'LINESTRING', 'POLYGON', 'MULTIPOINT',
            'MULTILINESTRING', 'MULTIPOLYGON', 'GEOMETRYCOLLECTION',
            'CIRCULARSTRING', 'COMPOUNDCURVE', 'CURVEPOLYGON',
            'MULTICURVE', 'MULTISURFACE', 'TRIANGLE', 'TIN',
            'POLYHEDRALSURFACE'
        ]
        upper_sample = sample.upper()
        for wkt_type in wkt_types:
            if upper_sample.startswith(wkt_type):
                # Check if it's followed by space, Z, M, ZM, or (
                rest = upper_sample[len(wkt_type):]
                if not rest or rest[0] in ' (ZM':
                    return GeometryFormat.WKT
        
        # GeoJSON: JSON with "type" and "coordinates" or "geometries"
        if sample.startswith('{'):
            try:
                parsed = json.loads(sample)
                if isinstance(parsed, dict):
                    if 'type' in parsed and ('coordinates' in parsed or 'geometries' in parsed):
                        return GeometryFormat.GEOJSON
                    if 'arcs' in parsed or 'objects' in parsed:
                        return GeometryFormat.TOPOJSON
            except json.JSONDecodeError:
                pass
        
        # KML: XML with Point, LineString, Polygon, etc.
        if sample.startswith('<') or '<coordinates' in sample.lower():
            kml_elements = ['<point', '<linestring', '<polygon', '<multigeometry', 
                           '<linearring', '<coordinates']
            lower_sample = sample.lower()
            if any(elem in lower_sample for elem in kml_elements):
                return GeometryFormat.KML
        
        # Earth Engine: ee.Geometry pattern
        if sample.startswith('ee.Geometry'):
            return GeometryFormat.EARTH_ENGINE
        
        # WKB/EWKB: hex string (only hex chars, even length)
        if len(sample) >= 2 and len(sample) % 2 == 0:
            if all(c in '0123456789ABCDEFabcdef' for c in sample):
                # Check for EWKB - has SRID flag in byte 5
                # First byte is byte order (01 = little endian, 00 = big endian)
                # Bytes 2-5 are geometry type (with SRID flag)
                try:
                    if len(sample) >= 10:
                        # For little endian, check if SRID flag (0x20) is set
                        type_bytes = sample[2:10]
                        type_int = int(type_bytes, 16)
                        # Little endian, so we need to reverse bytes
                        if sample[0:2].lower() == '01':
                            # Little endian - reverse the bytes
                            type_int = int(''.join(reversed([type_bytes[i:i+2] for i in range(0, 8, 2)])), 16)
                        if type_int & 0x20000000:  # SRID flag
                            return GeometryFormat.EWKB
                    return GeometryFormat.WKB
                except ValueError:
                    pass
        
        return GeometryFormat.UNKNOWN
    
    @staticmethod
    def parse(value: str, format_type: str, srid: int = 4326, 
              x_value: Optional[float] = None, y_value: Optional[float] = None) -> Optional[QgsGeometry]:
        """
        Parse a geometry string into a QgsGeometry object.
        
        :param value: Geometry string to parse
        :param format_type: Geometry format (from GeometryFormat)
        :param srid: Spatial reference ID (used for some formats)
        :param x_value: X coordinate (for XY format)
        :param y_value: Y coordinate (for XY format)
        :return: QgsGeometry object or None if parsing fails
        """
        if format_type == GeometryFormat.XY:
            return GeometryParser._parse_xy(x_value, y_value)
        
        if not value or not isinstance(value, str):
            return None
            
        value = value.strip()
        if not value:
            return None
        
        try:
            if format_type == GeometryFormat.WKT:
                return GeometryParser._parse_wkt(value)
            elif format_type == GeometryFormat.WKB:
                return GeometryParser._parse_wkb(value)
            elif format_type == GeometryFormat.EWKT:
                return GeometryParser._parse_ewkt(value)
            elif format_type == GeometryFormat.EWKB:
                return GeometryParser._parse_ewkb(value)
            elif format_type in (GeometryFormat.GEOJSON, GeometryFormat.JSON):
                return GeometryParser._parse_geojson(value)
            elif format_type == GeometryFormat.KML:
                return GeometryParser._parse_kml(value)
            elif format_type == GeometryFormat.EARTH_ENGINE:
                return GeometryParser._parse_earth_engine(value)
            elif format_type == GeometryFormat.TOPOJSON:
                return GeometryParser._parse_topojson(value)
            else:
                QgsMessageLog.logMessage(
                    f"Unknown geometry format: {format_type}",
                    'CSV Geometry Import', Qgis.Warning
                )
                return None
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error parsing geometry: {str(e)}",
                'CSV Geometry Import', Qgis.Warning
            )
            return None
    
    @staticmethod
    def _parse_wkt(value: str) -> Optional[QgsGeometry]:
        """Parse WKT geometry string"""
        geom = QgsGeometry.fromWkt(value)
        if geom.isNull() or geom.isEmpty():
            return None
        return geom
    
    @staticmethod
    def _parse_wkb(value: str) -> Optional[QgsGeometry]:
        """Parse WKB hex string"""
        try:
            wkb_bytes = binascii.unhexlify(value)
            geom = QgsGeometry()
            geom.fromWkb(wkb_bytes)
            if geom.isNull() or geom.isEmpty():
                return None
            return geom
        except (binascii.Error, ValueError) as e:
            QgsMessageLog.logMessage(
                f"WKB parsing error: {str(e)}",
                'CSV Geometry Import', Qgis.Warning
            )
            return None
    
    @staticmethod
    def _parse_ewkt(value: str) -> Tuple[Optional[QgsGeometry], Optional[int]]:
        """
        Parse EWKT (Extended WKT with SRID).
        Format: SRID=4326;POINT(0 0)
        
        :return: Tuple of (geometry, srid)
        """
        match = re.match(r'SRID=(\d+);(.+)', value, re.IGNORECASE)
        if match:
            srid = int(match.group(1))
            wkt_part = match.group(2)
            geom = GeometryParser._parse_wkt(wkt_part)
            return geom
        return None
    
    @staticmethod
    def _parse_ewkb(value: str) -> Optional[QgsGeometry]:
        """
        Parse EWKB (Extended WKB with SRID embedded).
        The SRID is encoded in the type bytes with flag 0x20000000.
        """
        try:
            wkb_bytes = binascii.unhexlify(value)
            geom = QgsGeometry()
            geom.fromWkb(wkb_bytes)
            if geom.isNull() or geom.isEmpty():
                return None
            return geom
        except (binascii.Error, ValueError) as e:
            QgsMessageLog.logMessage(
                f"EWKB parsing error: {str(e)}",
                'CSV Geometry Import', Qgis.Warning
            )
            return None
    
    @staticmethod
    def _parse_geojson(value: str) -> Optional[QgsGeometry]:
        """Parse GeoJSON geometry object"""
        try:
            geojson = json.loads(value)
            
            # Handle Feature wrapper
            if geojson.get('type') == 'Feature':
                geojson = geojson.get('geometry', {})
            
            geom_type = geojson.get('type', '').lower()
            coords = geojson.get('coordinates', [])
            
            if geom_type == 'point':
                if len(coords) >= 2:
                    return QgsGeometry.fromPointXY(QgsPointXY(coords[0], coords[1]))
            
            elif geom_type == 'multipoint':
                points = [QgsPointXY(c[0], c[1]) for c in coords if len(c) >= 2]
                if points:
                    return QgsGeometry.fromMultiPointXY(points)
            
            elif geom_type == 'linestring':
                points = [QgsPointXY(c[0], c[1]) for c in coords if len(c) >= 2]
                if len(points) >= 2:
                    return QgsGeometry.fromPolylineXY(points)
            
            elif geom_type == 'multilinestring':
                lines = []
                for line in coords:
                    points = [QgsPointXY(c[0], c[1]) for c in line if len(c) >= 2]
                    if len(points) >= 2:
                        lines.append(points)
                if lines:
                    return QgsGeometry.fromMultiPolylineXY(lines)
            
            elif geom_type == 'polygon':
                rings = []
                for ring in coords:
                    points = [QgsPointXY(c[0], c[1]) for c in ring if len(c) >= 2]
                    if len(points) >= 3:
                        rings.append(points)
                if rings:
                    return QgsGeometry.fromPolygonXY(rings)
            
            elif geom_type == 'multipolygon':
                polygons = []
                for polygon in coords:
                    rings = []
                    for ring in polygon:
                        points = [QgsPointXY(c[0], c[1]) for c in ring if len(c) >= 2]
                        if len(points) >= 3:
                            rings.append(points)
                    if rings:
                        polygons.append(rings)
                if polygons:
                    return QgsGeometry.fromMultiPolygonXY(polygons)
            
            elif geom_type == 'geometrycollection':
                geometries = geojson.get('geometries', [])
                geom_list = []
                for g in geometries:
                    parsed = GeometryParser._parse_geojson(json.dumps(g))
                    if parsed:
                        geom_list.append(parsed)
                if geom_list:
                    # Combine geometries
                    combined = geom_list[0]
                    for g in geom_list[1:]:
                        combined = combined.combine(g)
                    return combined
            
            return None
            
        except json.JSONDecodeError as e:
            QgsMessageLog.logMessage(
                f"GeoJSON parsing error: {str(e)}",
                'CSV Geometry Import', Qgis.Warning
            )
            return None
    
    @staticmethod
    def _parse_kml(value: str) -> Optional[QgsGeometry]:
        """Parse KML geometry element"""
        try:
            # Wrap in root element if needed
            if not value.strip().startswith('<?xml') and not value.strip().lower().startswith('<kml'):
                value = f'<root xmlns:gx="http://www.google.com/kml/ext/2.2">{value}</root>'
            
            root = ET.fromstring(value)
            
            # Find coordinates element
            coords_elem = None
            for elem in root.iter():
                if elem.tag.lower().endswith('coordinates') or elem.tag == 'coordinates':
                    coords_elem = elem
                    break
            
            if coords_elem is None or coords_elem.text is None:
                return None
            
            # Parse coordinates (format: lon,lat,alt lon,lat,alt ...)
            coords_text = coords_elem.text.strip()
            coord_pairs = coords_text.split()
            
            points = []
            for pair in coord_pairs:
                parts = pair.split(',')
                if len(parts) >= 2:
                    try:
                        lon = float(parts[0])
                        lat = float(parts[1])
                        points.append(QgsPointXY(lon, lat))
                    except ValueError:
                        continue
            
            if not points:
                return None
            
            # Determine geometry type from parent element
            parent_tag = ''
            for elem in root.iter():
                for child in elem:
                    if child.tag.lower().endswith('coordinates') or child.tag == 'coordinates':
                        parent_tag = elem.tag.lower()
                        break
            
            # Remove namespace prefix
            if '}' in parent_tag:
                parent_tag = parent_tag.split('}')[1]
            
            if 'point' in parent_tag and len(points) >= 1:
                return QgsGeometry.fromPointXY(points[0])
            elif 'linestring' in parent_tag and len(points) >= 2:
                return QgsGeometry.fromPolylineXY(points)
            elif ('polygon' in parent_tag or 'linearring' in parent_tag) and len(points) >= 3:
                return QgsGeometry.fromPolygonXY([points])
            elif len(points) == 1:
                return QgsGeometry.fromPointXY(points[0])
            elif len(points) >= 3 and points[0] == points[-1]:
                return QgsGeometry.fromPolygonXY([points])
            elif len(points) >= 2:
                return QgsGeometry.fromPolylineXY(points)
            
            return None
            
        except ET.ParseError as e:
            QgsMessageLog.logMessage(
                f"KML parsing error: {str(e)}",
                'CSV Geometry Import', Qgis.Warning
            )
            return None
    
    @staticmethod
    def _parse_earth_engine(value: str) -> Optional[QgsGeometry]:
        """
        Parse Earth Engine geometry format.
        Examples:
        - ee.Geometry.Point([lon, lat])
        - ee.Geometry.Polygon([[[lon, lat], [lon, lat], ...]])
        - ee.Geometry.Rectangle([west, south, east, north])
        """
        try:
            # Extract geometry type and coordinates
            match = re.match(
                r'ee\.Geometry\.(\w+)\s*\(\s*(\[.+\])\s*\)',
                value.strip(),
                re.DOTALL
            )
            
            if not match:
                # Try alternate format with dict
                if '{' in value and 'coordinates' in value:
                    # Extract JSON part
                    json_match = re.search(r'\{[^}]+\}', value)
                    if json_match:
                        return GeometryParser._parse_geojson(json_match.group())
                return None
            
            geom_type = match.group(1).lower()
            coords_str = match.group(2)
            
            # Parse coordinates as JSON array
            coords = json.loads(coords_str)
            
            if geom_type == 'point':
                if len(coords) >= 2:
                    return QgsGeometry.fromPointXY(QgsPointXY(coords[0], coords[1]))
            
            elif geom_type == 'multipoint':
                points = [QgsPointXY(c[0], c[1]) for c in coords if len(c) >= 2]
                if points:
                    return QgsGeometry.fromMultiPointXY(points)
            
            elif geom_type == 'linestring':
                points = [QgsPointXY(c[0], c[1]) for c in coords if len(c) >= 2]
                if len(points) >= 2:
                    return QgsGeometry.fromPolylineXY(points)
            
            elif geom_type == 'linearring':
                points = [QgsPointXY(c[0], c[1]) for c in coords if len(c) >= 2]
                if len(points) >= 3:
                    return QgsGeometry.fromPolygonXY([points])
            
            elif geom_type == 'polygon':
                # coords is [[[x,y], [x,y], ...]] for polygon
                if coords and isinstance(coords[0], list):
                    if coords[0] and isinstance(coords[0][0], list):
                        # Multi-ring polygon
                        rings = []
                        for ring in coords:
                            points = [QgsPointXY(c[0], c[1]) for c in ring if len(c) >= 2]
                            if len(points) >= 3:
                                rings.append(points)
                        if rings:
                            return QgsGeometry.fromPolygonXY(rings)
                    else:
                        # Single ring
                        points = [QgsPointXY(c[0], c[1]) for c in coords if len(c) >= 2]
                        if len(points) >= 3:
                            return QgsGeometry.fromPolygonXY([points])
            
            elif geom_type == 'multipolygon':
                polygons = []
                for polygon in coords:
                    rings = []
                    for ring in polygon:
                        points = [QgsPointXY(c[0], c[1]) for c in ring if len(c) >= 2]
                        if len(points) >= 3:
                            rings.append(points)
                    if rings:
                        polygons.append(rings)
                if polygons:
                    return QgsGeometry.fromMultiPolygonXY(polygons)
            
            elif geom_type == 'rectangle' or geom_type == 'bbox':
                # [west, south, east, north]
                if len(coords) >= 4:
                    west, south, east, north = coords[0], coords[1], coords[2], coords[3]
                    points = [
                        QgsPointXY(west, south),
                        QgsPointXY(east, south),
                        QgsPointXY(east, north),
                        QgsPointXY(west, north),
                        QgsPointXY(west, south)
                    ]
                    return QgsGeometry.fromPolygonXY([points])
            
            return None
            
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            QgsMessageLog.logMessage(
                f"Earth Engine parsing error: {str(e)}",
                'CSV Geometry Import', Qgis.Warning
            )
            return None
    
    @staticmethod
    def _parse_topojson(value: str) -> Optional[QgsGeometry]:
        """
        Parse TopoJSON geometry.
        Note: Full TopoJSON support requires resolving arc references.
        This implementation handles simple cases and extracted geometries.
        """
        try:
            topo = json.loads(value)
            
            # If it's a simple geometry object with coordinates (already resolved)
            if 'type' in topo and 'coordinates' in topo:
                return GeometryParser._parse_geojson(value)
            
            # If it has arcs, we need to resolve them
            arcs = topo.get('arcs', [])
            objects = topo.get('objects', {})
            
            if not objects:
                return None
            
            # Get the first object
            first_obj_name = list(objects.keys())[0]
            first_obj = objects[first_obj_name]
            
            # Resolve geometry
            return GeometryParser._resolve_topojson_geometry(first_obj, arcs)
            
        except (json.JSONDecodeError, ValueError) as e:
            QgsMessageLog.logMessage(
                f"TopoJSON parsing error: {str(e)}",
                'CSV Geometry Import', Qgis.Warning
            )
            return None
    
    @staticmethod
    def _resolve_topojson_geometry(obj: dict, arcs: list) -> Optional[QgsGeometry]:
        """Resolve TopoJSON geometry using arc references"""
        geom_type = obj.get('type', '').lower()
        
        if geom_type == 'point':
            coords = obj.get('coordinates', [])
            if len(coords) >= 2:
                return QgsGeometry.fromPointXY(QgsPointXY(coords[0], coords[1]))
        
        elif geom_type == 'multipoint':
            coords = obj.get('coordinates', [])
            points = [QgsPointXY(c[0], c[1]) for c in coords if len(c) >= 2]
            if points:
                return QgsGeometry.fromMultiPointXY(points)
        
        elif geom_type in ('linestring', 'multilinestring', 'polygon', 'multipolygon'):
            arc_indices = obj.get('arcs', [])
            resolved_coords = GeometryParser._resolve_arcs(arc_indices, arcs)
            
            if geom_type == 'linestring' and resolved_coords:
                points = [QgsPointXY(c[0], c[1]) for c in resolved_coords[0] if len(c) >= 2]
                if len(points) >= 2:
                    return QgsGeometry.fromPolylineXY(points)
            
            elif geom_type == 'multilinestring' and resolved_coords:
                lines = []
                for line_coords in resolved_coords:
                    points = [QgsPointXY(c[0], c[1]) for c in line_coords if len(c) >= 2]
                    if len(points) >= 2:
                        lines.append(points)
                if lines:
                    return QgsGeometry.fromMultiPolylineXY(lines)
            
            elif geom_type == 'polygon' and resolved_coords:
                rings = []
                for ring_coords in resolved_coords:
                    points = [QgsPointXY(c[0], c[1]) for c in ring_coords if len(c) >= 2]
                    if len(points) >= 3:
                        rings.append(points)
                if rings:
                    return QgsGeometry.fromPolygonXY(rings)
            
            elif geom_type == 'multipolygon' and resolved_coords:
                # For multipolygon, arcs is [[[arc_refs], ...], ...]
                polygons = []
                for poly_arcs in arc_indices:
                    poly_coords = GeometryParser._resolve_arcs(poly_arcs, arcs)
                    rings = []
                    for ring_coords in poly_coords:
                        points = [QgsPointXY(c[0], c[1]) for c in ring_coords if len(c) >= 2]
                        if len(points) >= 3:
                            rings.append(points)
                    if rings:
                        polygons.append(rings)
                if polygons:
                    return QgsGeometry.fromMultiPolygonXY(polygons)
        
        elif geom_type == 'geometrycollection':
            geometries = obj.get('geometries', [])
            geom_list = []
            for g in geometries:
                parsed = GeometryParser._resolve_topojson_geometry(g, arcs)
                if parsed:
                    geom_list.append(parsed)
            if geom_list:
                combined = geom_list[0]
                for g in geom_list[1:]:
                    combined = combined.combine(g)
                return combined
        
        return None
    
    @staticmethod
    def _resolve_arcs(arc_refs: list, arcs: list) -> list:
        """
        Resolve arc references to coordinate arrays.
        Arc references can be positive (forward) or negative (reverse).
        """
        resolved = []
        
        for ref_group in arc_refs:
            if isinstance(ref_group, int):
                # Single arc reference
                ref_group = [ref_group]
            
            if not isinstance(ref_group, list):
                continue
            
            coords = []
            for ref in ref_group:
                if isinstance(ref, int):
                    arc_idx = ref if ref >= 0 else ~ref
                    if 0 <= arc_idx < len(arcs):
                        arc_coords = arcs[arc_idx][:]
                        # Decode delta-encoded coordinates
                        decoded = []
                        x, y = 0, 0
                        for point in arc_coords:
                            if len(point) >= 2:
                                x += point[0]
                                y += point[1]
                                decoded.append([x, y])
                        
                        if ref < 0:
                            decoded = decoded[::-1]
                        
                        # Avoid duplicate points at arc junctions
                        if coords and decoded and coords[-1] == decoded[0]:
                            decoded = decoded[1:]
                        coords.extend(decoded)
            
            if coords:
                resolved.append(coords)
        
        return resolved
    
    @staticmethod
    def _parse_xy(x_value: Optional[float], y_value: Optional[float]) -> Optional[QgsGeometry]:
        """Parse X-Y coordinate pair into Point geometry"""
        if x_value is None or y_value is None:
            return None
        
        try:
            x = float(x_value)
            y = float(y_value)
            return QgsGeometry.fromPointXY(QgsPointXY(x, y))
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def get_geometry_type_from_sample(samples: List[str], format_type: str) -> int:
        """
        Determine the geometry type from sample values.
        
        :param samples: List of sample geometry strings
        :param format_type: The geometry format
        :return: QgsWkbTypes geometry type
        """
        for sample in samples:
            if not sample:
                continue
            
            geom = GeometryParser.parse(sample, format_type)
            if geom and not geom.isNull():
                return geom.wkbType()
        
        # Default to unknown if we can't determine
        return QgsWkbTypes.Unknown
