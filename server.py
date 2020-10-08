from enlace import *	


class Server():	
    def __init__(self):	
        serial_name = "COM3"	
        self.com = enlace(serial_name)	
        self.com.enable()	
        self.readyServer = False	


    def receive_handshake(self):
        t1 = time.time()	
        while self.com.rx.getIsEmpty():	
            timeElapsed = time.time() - t1	
            if timeElapsed > 5:	
                print("Timeout. Encerrando comunicacao")	
                break	

        package = self.com.getData(14)	
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