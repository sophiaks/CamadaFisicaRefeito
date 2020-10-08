from enlace import *
from config import *
from textwrap import wrap
import math
import time
import logging
from crccheck.crc import Crc16
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


class Client():
    def __init__(self, filename):
        logging.info("Comecando Transmissao")
        serial_name = "COM4" 
        self.com = enlace(serial_name)
        self.com.enable()

        self.payloads = self.create_payloads(filename)
        self.n_packages = len(self.payloads)

        self.file_id = b'\x01'
        self.id_client = b'\x01'
        self.id_server = b'\x02'

        self.ready = False
        self.counter_timer = 0
        self.this_package = 1
        self.last_package_ok = b'\x00'
        self.n_error = b'\x00'

    def create_payloads(self, filename):
        with open(filename, 'rb') as f:
            data = f.read()
        return wrap(data, payloadSize)

    def create_crc(self, payload):
        crc = Crc16.calc(payload)
        crc = crc.to_bytes(2, byteorder="big")
        return crc

    def create_handshake(self, file_id):
        msg_type = b'\x01'
        n_packages = self.n_packages
        handshake = msg_type + self.id_client + self.id_server + n_packages + b'\x00' + b'\x00' + b'\x00' + crc 
        handshake = handshake + eop
        return handshake

    def get_handshake_conf(self):
        handshakeConf = self.com.getData(14)
        if handshakeConf[0] == 2:
            self.ready = True
        else:
            self.counter_timer += 1

    def send_handshake(self):
        logging.info("ENVIO HANDSHAKE")
        handshake = self.create_handshake(file_id)
        self.com.sendData(handshake)
        self.get_handshake_conf()
    
    def create_head(self, msg_type, n, n_error, last_package_ok):
        head = msg_type + self.id_client + self.id_server
        return head

    def create_package(self, head, this_package):
        logging.info("ENVIO PACOTE | TAMANHO: {0} | PACOTE: {1} | TOTAL PACOTES: {2} | CRC: 0".format(len(self.payloads[this_package]), self.this_package, len(self.payloads)))
        payload = head + self.payloads[this_package] + eop
        return payload

    def send_package(self, package):
        self.com.sendData(package)

    def get_package_confirmation(self):
        confirmation = self.com.getData(14)
        if confirmation[0] == 4:
            print("Pacote enviado e recebido com sucesso")

    def run_client(self):
        while not self.ready:
            timer1 = time.time()
            self.send_handshake()
        t1 = time.time()
        while self.this_package <= self.n_packages:
            head = self.create_head(b'\x03', self.this_package, self.n_error, self.last_package_ok)
            package = self.create_package(head, self.this_package)

            self.send_package(package)

            while self.com.rx.getIsEmpty():
                timeElapsed = time.time() - t1
                resposta = True
                if timeElapsed > 5:
                    resposta = False
                    print("Timeout. Encerrando comunicacao")
                    break
            if resposta:
                self.get_package_confirmation()
            self.this_package += 1

client = Client('oiakon.png')
client.run_client()

