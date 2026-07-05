#!/usr/bin/env python3

import http.client
import urllib.parse
import sys
import os
import argparse
from typing import Optional, Dict, Union, Tuple
import ssl

def simple_curl(url: str, method: str = "GET", headers: Optional[Dict] = None,
                data: Optional[Union[str, bytes]] = None, verify_ssl: bool = True,
                follow_redirects: bool = False, max_redirects: int = 5) -> tuple:
    """
    Send HTTP request to a URL, similar to curl functionality.

    Args:
        url: Full URL to send request to
        method: HTTP method (GET, POST, etc.)
        headers: Optional dictionary of headers
        data: Optional data to send with request
        verify_ssl: Whether to verify SSL certificates
        follow_redirects: Whether to follow HTTP redirects
        max_redirects: Maximum number of redirects to follow

    Returns:
        tuple: (status_code, headers, response_body)
    """
    redirects_count = 0
    current_url = url

    while True:
        # Parse URL
        parsed = urllib.parse.urlparse(current_url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query

        # Set up SSL context if needed
        context = None
        if parsed.scheme == "https":
            context = ssl.create_default_context()
            if not verify_ssl:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE

        # Create connection
        if parsed.scheme == "https":
            conn = http.client.HTTPSConnection(host, port, context=context)
        else:
            conn = http.client.HTTPConnection(host, port)

        # Prepare headers
        if headers is None:
            headers = {}
        if "User-Agent" not in headers:
            headers["User-Agent"] = "Python-Curl/1.0"

        try:
            # Send request
            conn.request(method, path, body=data, headers=headers)

            # Get response
            response = conn.getresponse()

            # Handle redirects
            if follow_redirects and response.status in (301, 302, 303, 307, 308):
                if redirects_count >= max_redirects:
                    raise Exception(f"Too many redirects (max: {max_redirects})")

                redirects_count += 1
                location = response.getheader('Location')

                # Handle relative redirects
                if location.startswith('/'):
                    current_url = f"{parsed.scheme}://{parsed.netloc}{location}"
                else:
                    current_url = location

                # For 303, always use GET for the redirect
                if response.status == 303:
                    method = "GET"
                    data = None

                conn.close()
                continue

            # Read response
            body = response.read()

            return (response.status, response.getheaders(), body)

        finally:
            conn.close()

def get_remote_filename(url: str) -> str:
    """Extract filename from URL."""
    path = urllib.parse.urlparse(url).path
    return os.path.basename(path) or 'index.html'

def print_help() -> None:
    """Print detailed help information."""
    help_text = """
Python Curl - A simple curl clone

Usage: python script.py [options] URL

Options:
    -O, --remote-name         Write output to file named as remote file
    -o, --output <file>       Write to file instead of stdout
    -h, --help               Get help for commands
    -s, --silent             Silent mode
    -L, --location           Follow redirects
    -k, --insecure           Allow insecure server connections
    -X, --request <method>   Specify request method to use

Examples:
    {0} https://example.com
    {0} -O https://example.com/file.txt
    {0} -L -o output.txt https://example.com
    {0} -k -X POST https://example.com

Note: This is a simplified version of curl with basic functionality.
""".format(sys.argv[0])
    print(help_text)

def main():
    """Command line interface with argument parsing"""
    parser = argparse.ArgumentParser(description='Python Curl - A simple curl clone',
                                   add_help=False)  # Disable default help

    # Add arguments
    parser.add_argument('url', nargs='?', help='URL to fetch')
    parser.add_argument('-O', '--remote-name', action='store_true',
                       help='Write output to file named as remote file')
    parser.add_argument('-o', '--output', metavar='file',
                       help='Write to file instead of stdout')
    parser.add_argument('-h', '--help', action='store_true',
                       help='Get help for commands')
    parser.add_argument('-s', '--silent', action='store_true',
                       help='Silent mode')
    parser.add_argument('-L', '--location', action='store_true',
                       help='Follow redirects')
    parser.add_argument('-k', '--insecure', action='store_true',
                       help='Allow insecure server connections')
    parser.add_argument('-X', '--request', metavar='method',
                       help='Specify request method to use', default='GET')

    args = parser.parse_args()

    # Show help if requested or no URL provided
    if args.help or not args.url:
        print_help()
        sys.exit(0)

    try:
        # Make request
        status, headers, body = simple_curl(
            args.url,
            method=args.request,
            verify_ssl=not args.insecure,
            follow_redirects=args.location
        )

        # Handle output
        if args.remote_name:
            filename = get_remote_filename(args.url)
        elif args.output:
            filename = args.output
        else:
            filename = None

        # Write response
        if filename:
            with open(filename, 'wb') as f:
                f.write(body)
            if not args.silent:
                print(f"Downloaded to: {filename}")
        else:
            # Write to stdout
            if not args.silent:
                print(f"Status: {status}")
                print("\nHeaders:")
                for header in headers:
                    print(f"{header[0]}: {header[1]}")
                print("\nBody:")
            sys.stdout.buffer.write(body)

    except Exception as e:
        if not args.silent:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
