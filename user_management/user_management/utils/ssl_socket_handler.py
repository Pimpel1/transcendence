import ssl
import socket
from logging.handlers import SocketHandler


class SSLSocketHandler(SocketHandler):
    def __init__(self, host, port, ssl_certfile, ssl_keyfile):
        super().__init__(host, port)
        self.ssl_certfile = ssl_certfile
        self.ssl_keyfile = ssl_keyfile

    def makeSocket(self, timeout=1):
        sock = socket.create_connection((self.host, self.port))
        sock.settimeout(timeout)
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(
            certfile=self.ssl_certfile,
            keyfile=self.ssl_keyfile
        )
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context.wrap_socket(sock, server_hostname=self.host)

    def emit(self, record):
        try:
            msg = self.format(record) + "\n"
            self.send(msg.encode('utf-8'))
        except Exception:
            self.handleError(record)
