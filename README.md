# CSV Geometry Import - QGIS Plugin

A QGIS plugin to import CSV files containing geometry data in various formats that QGIS doesn't natively support.

## Features

### Supported Geometry Formats

| Format           | Description                | Example                                           |
| ---------------- | -------------------------- | ------------------------------------------------- |
| **WKT**          | Well-Known Text            | `POINT(30 10)`                                    |
| **WKB**          | Well-Known Binary (hex)    | `0101000000000000000000F03F...`                   |
| **EWKT**         | Extended WKT with SRID     | `SRID=4326;POINT(30 10)`                          |
| **EWKB**         | Extended WKB with SRID     | `0101000020E6100000...`                           |
| **GeoJSON**      | GeoJSON geometry object    | `{"type":"Point","coordinates":[30,10]}`          |
| **KML**          | KML geometry element       | `<Point><coordinates>30,10</coordinates></Point>` |
| **Earth Engine** | Google Earth Engine format | `ee.Geometry.Point([30, 10])`                     |
| **TopoJSON**     | TopoJSON geometry          | Arc-based topology format                         |
| **X-Y**          | Two columns (lon/lat)      | Separate X and Y columns                          |

### Key Features

- **Auto-detection**: Automatically detects geometry format from CSV content
- **CRS Selection**: Choose source coordinate reference system (default: EPSG:4326)
- **CSV Preview**: Preview first 10 rows before import
- **Multiple Delimiters**: Support for comma, semicolon, tab, pipe, and space
- **Encoding Options**: Wide range of character encodings supported
- **Invalid Geometry Handling**: Option to skip or import rows with invalid geometries
- **Memory Layer Creation**: Creates in-memory vector layer for fast access

## Installation

### From QGIS Plugin Manager

1. Open QGIS
2. Go to `Plugins` → `Manage and Install Plugins`
3. Search for "CSV Geometry Import"
4. Click `Install Plugin`

### Manual Installation

1. Download the plugin ZIP file
2. Extract to your QGIS plugins directory:
   - **Windows**: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
3. Restart QGIS
4. Enable the plugin in `Plugins` → `Manage and Install Plugins`

## Usage

1. Click the **CSV Geometry Import** button in the toolbar or go to `Vector` → `CSV Geometry Import` → `Import CSV with Geometry`

2. **Select CSV File**: Browse and select your CSV file

3. **Configure CSV Options**:
   - Delimiter (comma, semicolon, tab, etc.)
   - Character encoding
   - Whether first row contains headers

4. **Configure Geometry Options**:
   - Geometry format (auto-detect or manual selection)
   - Geometry column (for single column formats)
   - X and Y columns (for coordinate pair format)

5. **Set CRS**: Select the coordinate reference system of your data (default: EPSG:4326 - WGS 84)

6. **Layer Options**:
   - Set a name for the imported layer
   - Choose whether to add layer to map
   - Choose whether to skip invalid geometries

7. Click **Import** to create the layer

## Example CSV Files

### WKT Format
```csv
id,name,geometry
1,Location A,"POINT(77.5946 12.9716)"
2,Location B,"POINT(72.8777 19.0760)"
```

### GeoJSON Format
```csv
id,name,geom
1,Park,"{""type"":""Polygon"",""coordinates"":[[[0,0],[1,0],[1,1],[0,1],[0,0]]]}"
```

### X-Y Format
```csv
id,name,longitude,latitude
1,Delhi,77.1025,28.7041
2,Mumbai,72.8777,19.0760
```

### Earth Engine Format
```csv
id,name,ee_geometry
1,Study Area,"ee.Geometry.Rectangle([76.5, 28.0, 77.5, 29.0])"
```

## Requirements

- QGIS 3.0 or higher
- No additional Python packages required (uses standard library and QGIS/PyQt5)

## Author

**Mirjan Ali Sha**
- Email: mastools.help@gmail.com
- GitHub: [Mirjan-Ali-Sha](https://github.com/Mirjan-Ali-Sha)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### Version 1.0.0 (2025-12-21)
- Initial release
- Support for WKT, WKB, EWKT, EWKB formats
- GeoJSON/JSON geometry parsing
- KML geometry support
- Earth Engine geometry format
- TopoJSON support
- X-Y coordinate columns
- Auto-detection of geometry format
- CRS selection with EPSG:4326 default
