from enlace import *
import logging
from config import *
import sys

logging.basicConfig(filename='server.log', filemode='w', format='SERVER - %(asctime)s - %(message)s', level=logging.INFO)

class Server():	
    def __init__(self):	
        serial_name = "COM3"	
        self.com = enlace(serial_name)
        self.com.enable()
        self.readyServer = False
        
        self.n_packages = 0
        self.tamanho = None
        self.n_this_package = 0
        self.last_package_ok = b'\x00'

        self.id_client = b'\x01'
        self.id_server = b'\x02'
        self.eop = b'\xFF\xAA\xFF\xAA'
        self.msg = None
        self.package_order_ok = True

        self.crc = crc


        ################################################
        #__________________HANDSHAKE___________________#
        ################################################


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
                    logging.info(f"TIMEOUT {counterTimer}/4 | RX vazio")
                    counterTimer += 1
                    t1 = time.time()
                if counterTimer > 4:
                    print("Timeout. Encerrando comunicacao")
                    self.com.disable()
                    sys.exit()
                    break

        print("Servidor pronto para receber mensagem")
        
        package, _nPackage = self.com.getData(14)
        self.tamanho = package[5]
        self.n_packages = package[3]
        print(f"TOTAL DE PACOTES: {self.n_packages}")
        logging.info("RECEBIMENTO | TIPO: T1 (CONVITE HANDSHAKE) | TAMANHO: 14")
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
        self.com.sendData(handshake)


    def add_to_totalP(self, payload):
        '''
        Soma o payload recebido no payload existente
        '''
        if self.msg == None or len(self.msg) == 0:
            self.msg = payload
        else: 
            self.msg += payload
        # print(f"Total do payload: {len(self.msg)}\n\n")
        if len(self.msg) == self.tamanho:
            print("\nTodos os pacotes recebidos!\n")
            sys.exit()


    ####################################################
    #_______________ENVIO DE CONFIRMAÇÕES______________#
    ####################################################


    def send_package_conf(self):
        '''
        Envia a confirmação do pacote
        '''
        conf_head = b'\x04' + self.id_client + self.id_server + self.n_packages + b'\x00' +  b'\x00' + b'\x00' + bytes([self.n_this_package - 1]) + crc
        conf = conf_head + eop
        if (self.n_this_package - 1) <= int.from_bytes(self.n_packages, byteorder='big'):
            logging.info("ENVIO | TIPO: T4 (CONF) | TAMANHO TOTAL: 14")
            print(f"Enviando confirmacao do pacote {self.n_this_package - 1}")
            self.com.sendData(conf)

            if (self.n_this_package - 1) == int.from_bytes(self.n_packages, byteorder='big'):
                print("Nao precisa mandar conf do prox pacote")
                self.com.rx.clearBuffer()
                self.com.disable()
                sys.exit()

    def send_package_error(self, error_package):
        '''
        Envia uma mensagem de erro
        '''
        logging.info("ENVIO | TIPO: T6 (ERRO)| TAMANHO TOTAL: 14")
        print(f"\n\nEnviando mensagem para reenvio do pacote {error_package}\n\n")
        self.last_package_ok = bytes(self.last_package_ok)
        head_error = b'\x06' + self.id_client + self.id_server + self.n_packages + b'\x00' + bytes(error_package) + b'\x00' + (self.last_package_ok) + crc
        conf = head_error + eop
        print(conf)
        self.com.sendData(conf)


    ###############################################################
    #__________________________VERIFICAÇÕES_______________________#
    ###############################################################


    def check_order(self, head):
        '''
        Verifica se a ordem dos pacotes está certa
        '''
        if head[4] == (self.n_this_package):
            self.package_order_ok == True
            self.n_this_package += 1
            self.timer1 = time.time()
        else:
            print(f"Último pacote recebido: {self.n_this_package}, pacote recebido agora: {head[4]}")
            print(f"Pacote {head[4]} fora de ordem. Enviando mensagem de erro")
            self.send_package_error(head[4])
            self.package_order_ok = False


    def check_eop(self, head, eop):
        if eop == self.eop:
            print(f"EOP do pacote {self.n_this_package - 1} ok")
            if self.package_order_ok == True:
                self.send_package_conf()
                self.last_package_ok = head[5]
            else:
                print("EOP ok, erro na ordem dos pacotes")

        else:
            # print(f"eop do pacote {self.n_this_package} com erro, reenviar o pacote")
            self.send_package_error(self.n_this_package)
        pass

    #############################
    #________RECEBIMENTO________#
    #############################

    def receive_package(self):
        
        counter_timer_data = 0
        print("a")
        time.sleep(2)
        head = self.com.rx.getNData_T(10, self.timer1, counter_timer_data)

        logging.info(f"RECEBIMENTO | TIPO: T3 (DADOS) | TAMANHO: {head[5]} | PACOTE: {head[4]}/{head[3]} | CRC: {self.crc}")
        print(f"\nRecebendo {self.n_this_package}/{int.from_bytes(self.n_packages, byteorder = 'big')}\n")

        self.crc = head[8:9]

        if head == "DeuRuim":
            print("Timeout de 5s: tentando enviar mensagem novamente")
            
        elif head == "ENCERRADO":
            logging.info("ENVIO | TIPO: T5 (TIMEOUT 20s) | ENCERRANDO COMs")
            print("Timeout atingido: encerrando comunicacoes")
            head_timeout = b'\x05' + self.id_client + self.id_server + bytes([self.n_this_package]) + b'\x00' + b'\x00' + b'\x00' + self.last_package_ok + crc
            package_timeout = head_timeout + self.eop
            self.com.sendData(package_timeout)
            self.com.disable()
            sys.exit()
        else:
            self.check_order(head)
            payload, _nPayload = self.com.getData(head[5])
            if self.package_order_ok:
                self.add_to_totalP(payload)
            eop, _nEop = self.com.getData(4)
            print("o")
            self.check_eop(head, eop)
            time.sleep(1)
            if self.n_this_package == self.n_packages:
                print("Todos os pacotes recebidos, encerrando.")

    
            

        #--------------- MAIN ----------------#



    def runServer(self):
        while not self.readyServer:
            self.receive_handshake()
            # a = input("Quando quiser mandar a confirmacao do handshake dê enter")
            time.sleep(1)
            self.send_handshake_conf()
            print("\n___ HANDSHAKE OK ___\n")
            # self.com.rx.clearBuffer()
            # time.sleep(2)

        self.n_this_package = 1

        while self.n_this_package <= int.from_bytes(self.n_packages, byteorder='big'):
            self.timer1 = time.time()
            self.receive_package()
        sys.exit()

server = Server()	
server.runServer()