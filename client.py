from enlace import *
from config import *
from textwrap import wrap
import math
import time
import logging
from crccheck.crc import Crc16
import sys
logging.basicConfig(filename='client.log', filemode='w', format='CLIENT - %(asctime)s - %(message)s', level=logging.INFO)


class Client():
    def __init__(self, filename):
        logging.info("VAMOS COMECAR UHUL")
        serial_name = "COM4" 
        self.com = enlace(serial_name)
        self.com.enable()

        self.payloads = self.create_payloads(filename)
        self.n_packages = len(self.payloads)
        print(self.payloads)

        self.file_id = b'\x01'
        self.id_client = b'\x01'
        self.id_server = b'\x02'

        self.ready = False
        self.counter_timer = 0
        self.this_package = 1
        self.last_package_ok = b'\x00'
        self.n_error = b'\x00'

        self.crc = crc

    def divide_chunks(self, l, n):
        '''
        Divide a imagem em pedaços
        '''
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def create_payloads(self, filename):
        '''
        Cria os payloads e adiciona em uma lista
        '''
        with open(filename, 'rb') as f:
            data = f.read()
        self.size_total = len(data)
        payloads = list(self.divide_chunks(data, payloadSize))
        return payloads

    def create_crc(self, n):
        '''
        Cria o crc
        '''
        crc = Crc16.calc(self.payloads[n-1])
        crc = crc.to_bytes(2, byteorder="big")
        print(crc)
        return crc

    def create_handshake(self, file_id):
        '''
        Cria o handshake 
        '''
        msg_type = b'\x01'
        n_packages =  bytes([self.n_packages])
        handshake = msg_type + self.id_client + self.id_server + n_packages + b'\x00' +  b'\x01' + b'\x00' + b'\x00' + crc 
        handshake = handshake + eop
        return handshake

    def get_handshake_conf(self):
        '''
        Recebe a confirmação do handshake
        '''
        logging.info(f"RECEBIMENTO | TIPO: T2 | TAMANHO: 14")
        handshakeConf = self.com.getData(14)
        print("Peguei os bytes da conf")
        if handshakeConf[0] == 2:
            self.ready = True
        else:
            self.counter_timer += 1

    def send_handshake(self):
        '''
        Envia o handshake e espera a confirmação
        '''
        handshake = self.create_handshake(file_id)
        self.com.sendData(handshake)
        logging.info("ENVIO | TIPO: T1 | TAMANHO: 14")
        print("Handshake enviado")
        self.get_handshake_conf()
        print("Confirmacao do handshake recebida")
    
    def create_head(self, msg_type, n):
        '''
        Cria o head do pacote
        '''
        head = msg_type + self.id_client + self.id_server + bytes([self.n_packages]) + n.to_bytes(1, byteorder='big') + len(self.payloads[n-1]).to_bytes(1, byteorder='big') + b'\x00' + self.last_package_ok + crc
        return head

    def create_package(self, head, this_package):
        '''
        Monta o pacote
        '''
        payload = head + self.payloads[this_package - 1] + eop
        return payload

    def send_package(self, package):
        '''
        Envia o pacote
        '''
        logging.info(f"ENVIO | T3 (DADOS) | TAMANHO: {package[5]} | PACOTE: {self.this_package} | TOTAL PACOTES: {len(self.payloads)} | CRC: {self.crc}")
        self.com.sendData(package)

    def get_package_confirmation(self):
        '''
        Pega a confirmação do pacote
        '''
        confirmation, _nConf = self.com.getData(14)
        logging.info(f"RECEBIMENTO | T4 (CONF) | TAMANHO: {len(self.payloads[self.this_package- 1])} | PACOTE: {self.this_package} | TOTAL PACOTES: {len(self.payloads)} | CRC: {self.crc}")
        if confirmation[0] == 4:
            print(f"MENSAGEM T4 RECEBIDA - PACOTE {confirmation[7]}")
        elif confirmation[0] == 6:
            print("Erro no pacote {0}".format(confirmation[6]))
            head = self.create_head(b'\x03', confirmation[6])
            package = self.create_package(head, confirmation[6])
            self.send_package(package)
        if confirmation[7] == self.n_packages:
            print("\nTodos os pacotes foram enviados")
            self.com.disable
            sys.exit()

    def run_client(self):
        while not self.ready:
            timer1 = time.time()
            self.send_handshake()
            self.ready = True
        t1 = time.time()

        while self.this_package <= self.n_packages:
            head = self.create_head(b'\x03', self.this_package)
            print(len(head))
            package = self.create_package(head, self.this_package)

            print(f"____Pacote {self.this_package}____")

            self.send_package(package)
            print(f"Pacote {self.this_package} enviado")
            resposta = True

            while self.com.rx.getIsEmpty():
                timeElapsed = time.time() - t1
                resposta = True
                if timeElapsed > 5:
                    resposta = False
                    print("Timeout. Tentando novamente.")
                    break
            if resposta:
                self.get_package_confirmation()
                self.this_package += 1

            else:
                print(f"Nenhuma resposta recebida do pacote {self.this_package}")
                print(f"Enviando pacote {self.this_package} novamente.")
                self.send_package(package)
                t1 = time.time()
    
        if self.this_package == self.n_packages:
            self.com.rx.clearBuffer()
            print("TODOS OS PACOTES ENVIADOS")
            sys.exit()

client = Client('oiakon.png')
client.run_client()

