# CSV Geometry Import - QGIS Plugin

Import CSV files with various geometry formats that QGIS doesn't natively support. Part of **MAS Vector Processing** tools.

## Features

### Supported Geometry Formats

| Format           | Description                | Example                                           |
| ---------------- | -------------------------- | ------------------------------------------------- |
| **WKT**          | Well-Known Text            | `POINT(30 10)`                                    |
| **WKB**          | Well-Known Binary (hex)    | `0101000000...`                                   |
| **EWKT**         | Extended WKT with SRID     | `SRID=4326;POINT(30 10)`                          |
| **EWKB**         | Extended WKB with SRID     | `0101000020E6100000...`                           |
| **GeoJSON**      | GeoJSON geometry object    | `{"type":"Point","coordinates":[30,10]}`          |
| **KML**          | KML geometry element       | `<Point><coordinates>30,10</coordinates></Point>` |
| **Earth Engine** | Google Earth Engine format | `ee.Geometry.Point([30, 10])`                     |
| **TopoJSON**     | TopoJSON geometry          | Arc-based topology format                         |
| **X-Y**          | Two columns (lon/lat)      | Separate X and Y columns                          |

### Key Features

- **Auto-detection**: Automatically detects geometry format from CSV content
- **CRS Selection**: Choose coordinate reference system (default: EPSG:4326)
- **CSV Preview**: Preview first 10 rows before import
- **Multiple Delimiters**: Comma, semicolon, tab, pipe, space
- **Encoding Options**: Wide range of character encodings
- **Invalid Geometry Handling**: Skip or import with empty geometry
- **Detailed Report**: Create separate layers for NULL and Invalid geometries
- **Memory Layer**: Creates fast in-memory vector layer

## Installation

### From QGIS Plugin Manager
1. Go to `Plugins` → `Manage and Install Plugins`
2. Search for "CSV Geometry Import"
3. Click `Install Plugin`

### Manual Installation
1. Download the plugin ZIP file
2. Extract to your QGIS plugins directory:
   - **Windows**: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
3. Restart QGIS and enable the plugin

## Usage

1. Go to `MAS Vector Processing` → `CSV Geometry Import` or click toolbar button

2. **Select CSV File**: Browse and select your CSV file

3. **Configure CSV Options**:
   - Delimiter (comma, semicolon, tab, etc.)
   - Character encoding
   - First row contains headers

4. **Configure Geometry**:
   - Format (auto-detect or manual)
   - Geometry column or X-Y columns
   - Source CRS (default: EPSG:4326)

5. **Layer Options**:
   - Layer name
   - Skip invalid geometries
   - **Create detailed report** (creates _Null_Geom and _Invalid_Geom layers)

6. Click **Import**

## Configuration Options

| Option              | Description                               |
| ------------------- | ----------------------------------------- |
| **CSV File**        | Input CSV file path                       |
| **Delimiter**       | Comma, semicolon, tab, pipe, space        |
| **Encoding**        | UTF-8, Latin1, etc.                       |
| **Geometry Format** | Auto-detect or manual selection           |
| **Geometry Column** | Column containing geometry data           |
| **X/Y Columns**     | For coordinate pair format                |
| **CRS**             | Source coordinate reference system        |
| **Skip Invalid**    | Skip rows with invalid geometry           |
| **Detailed Report** | Create layers for NULL/Invalid geometries |

## Detailed Report Feature

When enabled, creates additional layers for debugging:

- **`<layer>_Null_Geom`**: Rows with empty/NULL geometry values
  - Contains: Row_Number + all original columns
  
- **`<layer>_Invalid_Geom`**: Rows where geometry parsing failed
  - Contains: Row_Number + all columns + Geom_Value (the problematic value)

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
1,Park,"{""type"":""Point"",""coordinates"":[77.5946,12.9716]}"
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
- No additional Python packages required

## Author

**Mirjan Ali Sha**
- Email: mastools.help@gmail.com
- GitHub: [Mirjan-Ali-Sha](https://github.com/Mirjan-Ali-Sha)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

### Version 1.0.1 (2024-12-21)
- Added "Create detailed report" option
- Separate tracking of NULL vs Invalid geometries
- Creates _Null_Geom and _Invalid_Geom layers for debugging
- Improved import statistics message

### Version 1.0.0 (2024-12-21)
- Initial release
- Support for WKT, WKB, EWKT, EWKB formats
- GeoJSON/JSON geometry parsing
- KML geometry support
- Earth Engine geometry format
- TopoJSON support
- X-Y coordinate columns
- Auto-detection of geometry format
- CRS selection with EPSG:4326 default
