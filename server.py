from enlace import *
import logging

logging.basicConfig(filename='server.log', filemode='a', format='SERVER - %(asctime)s - %(message)s', level=logging.INFO)


class Server():	
    def __init__(self):	
        serial_name = "COM3"	
        self.com = enlace(serial_name)
        self.com.enable()
        self.readyServer = False


    def receive_handshake(self):
        t1 = time.time()
        counterTimer = 1	
        while self.com.rx.getIsEmpty():	
            timeElapsed = time.time() - t1
            if timeElapsed > 5:	
                print("Timeout. Tentando novamente")	
                counterTimer += 1
                t1 = time.time()
                if counterTimer > 4:
                    print("Timeout. Encerrando comunicacao")
                    self.com.disable()

        package = self.com.getData(14)
        logging.info("RECEBIMENTO | TIPO: T2 | TAMANHO TOTAL: ? | TOTAL DE PACOTES: ?")
        if package[0] == b'\x01':	
            print("cliente convidou para a transmissao")	

    def send_handshake_conf(self):	
        pass	

    def runServer(self):	
        while not self.readyServer:	
            self.receive_handshake()
            self.send_handshake_conf()


server = Server()	
server.runServer()