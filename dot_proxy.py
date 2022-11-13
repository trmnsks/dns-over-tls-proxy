import os
import socket
import socketserver
import ssl
import time


class TCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(self, server_address, resolver_address, RequestHandler):
        socketserver.TCPServer.__init__(self, server_address, RequestHandler)
        self.resolver_address = resolver_address


class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        msg = self.request.recv(4096)

        if msg:
            printfy("--> Received msg", self.client_address, bytes=msg)

            host, port = self.server.resolver_address  # type: ignore
            tls_sock = self.__get_tls_sock(host)

            with self.__tls_connect(tls_sock, host, port) as tls_con:
                answ = self.__forward_message(tls_con, msg)
                self.request.sendall(answ)
                printfy("---> Forwarded answ", self.client_address, bytes=answ)

    def __get_tls_sock(self, host):
        ssl_context = ssl.create_default_context()
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_sock = ssl_context.wrap_socket(tcp_sock, server_hostname=host)
        return ssl_sock

    def __tls_connect(self, sock, host, port, timeout=5):
        while True:
            try:
                sock.connect((host, port))
                printfy("---> Connected to", (host, port), tls=sock.version())
                return sock
            except Exception as e:
                print(f"Failed to connect: {e}")
                print(f"Retrying after: {timeout}s")
                time.sleep(timeout)

    def __forward_message(self, sock, msg):
        sock.sendall(msg)
        printfy("---> Forwarded msg", sock.server_hostname, bytes=msg)
        answ = sock.recv(4096)
        printfy("---> Received answ", sock.server_hostname, bytes=answ)
        return answ


def printfy(msg, addr, bytes=None, tls=None):
    if bytes:
        print(f"{msg} -> IP: {addr}, BYTES:{len(bytes)}")
    elif tls:
        print(f"{msg} -> IP: {addr}, {tls}")
    else:
        print(f"{msg} -> IP: {addr}")


if __name__ == "__main__":
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "53 "))
    DNS_HOST = os.environ.get("DNS_HOST", "1.1.1.1")
    DNS_PORT = int(os.environ.get("DNS_PORT", "853"))

    with TCPServer((HOST, PORT), (DNS_HOST, DNS_PORT), TCPHandler) as server:
        printfy("-> TCP server started", (HOST, PORT))
        printfy("-> DNS to forward to", (DNS_HOST, DNS_PORT))
        server.serve_forever()
