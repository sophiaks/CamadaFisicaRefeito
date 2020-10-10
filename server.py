from enlace import *
import logging
from config import *
import sys

logging.basicConfig(filename='server.log', filemode='a', format='SERVER - %(asctime)s - %(message)s', level=logging.INFO)

class Server():	
    def __init__(self):	
        serial_name = "COM3"	
        self.com = enlace(serial_name)
        self.com.enable()
        self.readyServer = False
        
        self.n_packages = 0
        self.tamanho = None
        self.n_this_package = 1

        self.id_client = b'\x01'
        self.id_server = b'\x02'
        self.eop = b'\xFF\xAA\xFF\xAA'
        self.msg = None
        self.package_order_ok = True


    def receive_handshake(self):
        '''
        Recebe o handshake
        '''
        t1 = time.time()
        counterTimer = 1	
        if self.readyServer == False:
            while self.com.rx.getIsEmpty():	
                timeElapsed = time.time() - t1
                if timeElapsed > 5:
                    print("Timeout. Tentando novamente")	
                    counterTimer += 1
                    t1 = time.time()
                if counterTimer > 4:
                    print("Timeout. Encerrando comunicacao")
                    self.com.disable()
                    sys.exit()
                    break

        print("Servidor pronto para receber mensagem")
        
        package, _nPackage = self.com.getData(14)
        print(package)
        self.tamanho = package[5]
        self.n_packages = package[3]
        logging.info("RECEBIMENTO | TIPO: T2 (HANDSHAKE) | TAMANHO: 14")
        print(package[0])
        if package[0] == 1:
            print("Cliente convidando para a transmissao")	
            self.readyServer = True


    def create_handshake_conf(self):
        '''
        Cria a confirmação do handshake
        '''
        msg_type = b'\x02'
        self.n_packages =  bytes([self.n_packages])
        handshake = msg_type + self.id_client + self.id_server + self.n_packages + b'\x01' + b'\x00' + b'\x00' + b'\x00' + crc 
        handshake = handshake + eop
        return handshake


    def send_handshake_conf(self):
        '''
        Manda a confirmação do handshake
        '''
        logging.info("ENVIO | TIPO: T2 (CONF HANDSHAKE) | TAMANHO TOTAL: 14")
        handshake = self.create_handshake_conf()
        print("HandshakeConf")
        print(handshake)
        self.com.sendData(handshake)


    def send_package_conf(self):
        '''
        Envia a confirmação do pacote
        '''
        logging.info("ENVIO | TIPO: T4| TAMANHO TOTAL: 14")
        print(f"Enviando confirmacao do pacote {self.n_this_package}")
        conf_head = b'\x04' + self.id_client + self.id_server + self.n_packages + b'\x00' +  b'\x00' + b'\x00' + bytes([self.n_this_package]) + crc
        conf = conf_head + eop
        self.com.sendData(conf)


    def add_to_totalP(self, payload):
        '''
        Soma o payload recebido no payload existente
        '''
        if self.msg == None or len(self.msg) == 0:
            self.msg = payload
        else: 
            self.msg += payload
        print(f"Total do payload: {len(self.msg)}")
        if len(self.msg) == self.tamanho:
            print("Todos os pacotes recebidos!")
            sys.exit()


    def check_order(self, head):
        '''
        Verifica se a ordem dos pacotes está certa
        '''
        if head[4] == (self.n_this_package - 1):
            self.package_order_ok == True
        else:
            print(f"Último pacote recebido: {self.n_this_package}, pacote recebido agora: {head[4]}")

    def check_eop(self, head, eop):
        if eop == self.eop:
            print("eop ok")
        pass


    def receive_package(self):
        time_elapsed_data = time.time()
        counter_timer_data = 0
        logging.info("RECEBIMENTO | TIPO: T5 | ")
        head = self.com.rx.getNData_T(10, time_elapsed_data, counter_timer_data)
        self.check_order(head)
        self.n_this_package = head[4]
        print(f"Recebendo pacote {self.n_this_package}")

        if head == "DeuRuim":
            logging.warning("ENVIO | TIPO: T5 (TIMEOUT 5s)")
            print("Timeout de 5s: tentando enviar mensagem novamente")
            #TO_DO
            head_timeout = "opa"
        elif head == "ENCERRADO":
            logging.warning("ENVIO | TIPO: T5 (TIMEOUT 20s) | ENCERRANDO COMs")
            print("Timeout atingido: encerrando comunicacoes")
            self.com.disable()
            sys.exit()
        else:
            payload, _nPayload = self.com.getData(head[5])
            self.add_to_totalP(payload)
            self.send_package_conf()
            eop, _nEop = self.com.getData(4)
            if eop == self.eop:
                print("eop recebido com sucesso")


    def runServer(self):
        while not self.readyServer:
            self.receive_handshake()
            print("Handshake recebido")
            self.send_handshake_conf()
            print("Confirmacao enviada")

        while self.n_this_package < int.from_bytes(self.n_packages, byteorder='big'):
            print(self.n_this_package, self.n_packages)
            self.receive_package()
        sys.exit()

server = Server()	
server.runServer()