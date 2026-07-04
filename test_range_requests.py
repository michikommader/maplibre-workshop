#!/usr/bin/env python3
"""
Test script to verify HTTP Range Request support.
Tests the PMTiles server with various range requests.
"""

import requests
import sys


def test_range_requests(url):
    """Test range request support."""
    print(f"Testing range requests on: {url}\n")
    
    # Test 1: HEAD request to get file size
    print("Test 1: Get file metadata (HEAD request)")
    try:
        response = requests.head(url, timeout=5)
        file_size = response.headers.get('Content-Length')
        accept_ranges = response.headers.get('Accept-Ranges')
        
        print(f"  Status: {response.status_code}")
        print(f"  Content-Length: {file_size}")
        print(f"  Accept-Ranges: {accept_ranges}")
        print(f"  ✓ Server advertises range support\n" if accept_ranges == 'bytes' else "  ✗ No range support advertised\n")
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return False
    
    if not file_size or accept_ranges != 'bytes':
        print("Server does not support range requests")
        return False
    
    file_size = int(file_size)
    
    # Test 2: Request first 1KB
    print("Test 2: Request first 1024 bytes (0-1023)")
    try:
        response = requests.get(url, headers={'Range': 'bytes=0-1023'}, timeout=5)
        print(f"  Status: {response.status_code}")
        print(f"  Content-Range: {response.headers.get('Content-Range')}")
        print(f"  Content-Length: {len(response.content)}")
        print(f"  ✓ Partial content received\n" if response.status_code == 206 else "  ✗ Unexpected status\n")
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return False
    
    # Test 3: Request middle range
    mid_start = file_size // 2
    mid_end = min(mid_start + 1023, file_size - 1)
    print(f"Test 3: Request middle range ({mid_start}-{mid_end})")
    try:
        response = requests.get(url, headers={'Range': f'bytes={mid_start}-{mid_end}'}, timeout=5)
        print(f"  Status: {response.status_code}")
        print(f"  Content-Range: {response.headers.get('Content-Range')}")
        print(f"  Content-Length: {len(response.content)}")
        print(f"  ✓ Partial content received\n" if response.status_code == 206 else "  ✗ Unexpected status\n")
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return False
    
    # Test 4: Request last 1KB (suffix range)
    print("Test 4: Request last 1024 bytes (suffix range)")
    try:
        response = requests.get(url, headers={'Range': 'bytes=-1024'}, timeout=5)
        print(f"  Status: {response.status_code}")
        print(f"  Content-Range: {response.headers.get('Content-Range')}")
        print(f"  Content-Length: {len(response.content)}")
        print(f"  ✓ Partial content received\n" if response.status_code == 206 else "  ✗ Unexpected status\n")
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return False
    
    # Test 5: Request invalid range (should get 416)
    print("Test 5: Request invalid range (should get 416 error)")
    try:
        response = requests.get(url, headers={'Range': 'bytes=9999999999-9999999999'}, timeout=5)
        print(f"  Status: {response.status_code}")
        print(f"  ✓ Correctly rejected invalid range\n" if response.status_code == 416 else "  ✗ Unexpected response\n")
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
    
    print("All tests completed! ✓")
    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 test_range_requests.py <url>")
        print("Example: python3 test_range_requests.py http://localhost:8000/archive.pmtiles")
        sys.exit(1)
    
    url = sys.argv[1]
    success = test_range_requests(url)
    sys.exit(0 if success else 1)
