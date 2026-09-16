"""
Mini HTTP Web Server — TCP Socket Programming
================================================
COMP-3315 | Network Socket Programming | UCAS - Gaza
Author: Eng. Mohanad Abu Ammar

A lightweight, single-threaded HTTP/1.1 server built directly on Python's
low-level `socket` module — no frameworks, no libraries. It listens on a
TCP port, accepts connections from any standard web browser, parses the
raw HTTP GET request, and returns the requested static HTML file (or a
proper error response if something goes wrong).

Socket lifecycle implemented below:

    socket()  ->  bind()  ->  listen()  ->  accept()  ->  recv() / send()  ->  close()

Why TCP (SOCK_STREAM) and not UDP:
    HTTP/1.1 requires a reliable, ordered byte stream — a single dropped or
    reordered packet would corrupt the HTML response. TCP's connection-oriented
    handshake guarantees delivery order, which is exactly the contract HTTP
    depends on.
"""

import socket

HOST = ""                    # Bind to all available network interfaces
PORT = 8081                  # TCP port the server listens on
BACKLOG = 5                  # Max queued connections waiting to be accept()-ed
DEFAULT_FILE = "index.html"  # Served automatically when the browser requests "/"
BUFFER_SIZE = 1024           # Bytes read per recv() call


def build_response(status_line: str, content_type: str, body: str) -> bytes:
    """Assemble a complete, correctly-framed HTTP/1.1 response."""
    body_bytes = body.encode()
    headers = (
        f"{status_line}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body_bytes)}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    )
    return headers.encode() + body_bytes


def handle_request(connection_socket: socket.socket, address: tuple) -> None:
    """Read a single HTTP request from one client and reply to it."""
    try:
        # --- recv(): read the raw HTTP request text sent by the browser ---
        request = connection_socket.recv(BUFFER_SIZE).decode()
        if not request:
            return

        request_line = request.split("\r\n")[0]
        print(f"[{address[0]}:{address[1]}] {request_line}")

        # A valid request line looks like: "GET /index.html HTTP/1.1"
        parts = request_line.split()
        if len(parts) < 2:
            response = build_response(
                "HTTP/1.1 400 Bad Request", "text/plain", "400 - Bad Request"
            )
            connection_socket.send(response)
            return

        _method, path = parts[0], parts[1]
        filename = DEFAULT_FILE if path == "/" else path.lstrip("/")

        # --- File lookup: 200 OK on success, 404 on failure ---
        try:
            with open(filename, "r") as f:
                body = f.read()
            response = build_response("HTTP/1.1 200 OK", "text/html", body)
        except FileNotFoundError:
            response = build_response(
                "HTTP/1.1 404 Not Found", "text/plain", "404 - File Not Found"
            )

        # --- send(): write the response back over the same socket ---
        connection_socket.send(response)

    finally:
        # --- close(): every connection is closed after its one request/response cycle ---
        connection_socket.close()


def start_server() -> None:
    # --- socket(): create a TCP (SOCK_STREAM) socket using IPv4 (AF_INET) ---
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # --- bind(): reserve the port on all available interfaces ---
    server_socket.bind((HOST, PORT))

    # --- listen(): start accepting connections, with a small backlog queue ---
    server_socket.listen(BACKLOG)

    print(f"Server is ready to receive on port {PORT} ...")
    print(f"Open: http://localhost:{PORT}/{DEFAULT_FILE}")

    try:
        while True:
            # --- accept(): block until a browser connects ---
            connection_socket, address = server_socket.accept()
            handle_request(connection_socket, address)
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server()
