# PMTiles HTTP Range Request Server

A Python HTTP server with full support for HTTP Range requests, essential for efficient PMTiles serving.

## Why Range Requests Matter for PMTiles

PMTiles archives are single files containing many map tiles at specific byte offsets. Without Range request support:
- The entire PMTiles file would be downloaded for each tile request
- Performance would be extremely poor
- Bandwidth usage would be excessive

With Range request support:
- Only the requested byte range is transferred
- Efficient and fast tile delivery
- Minimal bandwidth usage

## Usage

### Basic Usage (Current Directory)
```bash
python3 pmtiles_server.py
# Server runs on http://localhost:8000
```

### Custom Port
```bash
python3 pmtiles_server.py 8080
# Server runs on http://localhost:8080
```

### Custom Directory
```bash
python3 pmtiles_server.py 8000 /path/to/pmtiles/directory
# Server runs on port 8000, serving from /path/to/pmtiles/directory
```

## Features

✅ **Full Range Request Support** - `206 Partial Content` responses  
✅ **Accept-Ranges Header** - Advertises range support to clients  
✅ **Security** - Prevents directory traversal attacks  
✅ **MIME Type Detection** - Proper content-type headers  
✅ **Logging** - Request logging with timestamps  
✅ **Error Handling** - Proper HTTP error codes (404, 416, etc.)

## Example: MapLibre Integration

```javascript
// MapLibre can now efficiently fetch tiles from your PMTiles archive
const map = new maplibregl.Map({
  container: 'map',
  style: {
    version: 8,
    sources: {
      pmtiles: {
        type: 'vector',
        url: 'http://localhost:8000/path/to/archive.pmtiles'
      }
    },
    layers: [/* ... */]
  }
});
```

## How Range Requests Work

1. **Client Request:**
   ```
   GET /archive.pmtiles HTTP/1.1
   Range: bytes=1024-2047
   ```

2. **Server Response:**
   ```
   HTTP/1.1 206 Partial Content
   Content-Range: bytes 1024-2047/1000000
   Content-Length: 1024
   Accept-Ranges: bytes
   
   [1024 bytes of data]
   ```

## Browser Compatibility

Range requests are supported by all modern browsers and HTTP clients including:
- MapLibre GL JS
- All modern web browsers
- cURL, wget
- fetch API

## Performance Tips

- Use SSD storage for PMTiles files (faster seeks)
- Monitor bandwidth: PMTiles with range requests typically use minimal bandwidth
- Enable gzip compression on application layer if needed (not built-in to keep server simple)

## Troubleshooting

### "416 Range Not Satisfiable"
- Check that the range values are valid and within file size
- Ensure client is requesting correct byte ranges

### "404 File Not found"
- Verify PMTiles file path is correct
- Check file permissions

### Slow Performance
- Ensure server is using proper port (avoid ports < 1024)
- Check network latency
- Monitor disk I/O with `iostat`
