from socket import *
from app_server import Ativo,Ordem,Sistema
import stockmarket_pb2
import time
import fcntl, os
import sys

# class CbSocket(poller.Callback):
#     def __init__(self, sock):
#         poller.Callback.__init__(self, sock, 10)
#         self.disable_timeout()

#     def handle(self):
#         msg = self.fd.recv(1024)
#         print("Recebido:", msg)

# class CbStdin(poller.Callback):
#     def __init__(self, sock):
#         poller.Callback.__init__(self, sys.stdin, 10)
#         self.disable_timeout()
#         self.sock = socks
#     def handle(self):
#         msg = self.fd.readline()
#         self.sock.send(msg.encode('utf8'))

class Server:
    def __init__(self):
        self.conectado = False
        self.usuario = ""
        self.notificar = True
        self.database_users = [
        ("Andrey", "123"),
        ("Iago", "456"),
        ("Sobral", "789")
        ]
        # self.databases_actions = [

        # ]

    def search(self, user, passwd):
        for i in range(len(self.database_users)):
            if self.database_users[i][0] == user:
                senha = self.database_users[i][1]
                if senha == passwd:
                    return True
        return False

    #def notifica(self, ordem):

if __name__ == '__main__': 
    s=Sistema()
    # o=Ordem(ativo='bidi4',preco=20)
    # s.cria_ativo(o)
    ativo_not = ""
    ip_bind = '0.0.0.0'
    port_bind = 5000
    srv = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
    srv.setsockopt(SOL_SOCKET,SO_REUSEADDR, 1)
    srv.bind((ip_bind, port_bind))
    srv.listen(2)
    server = Server()

    while True:
        print('Esperando conexão...')
        con,addr = srv.accept()
        #con.setblocking(0)
        #fcntl.fcntl(s, fcntl.F_SETFL, os.O_NONBLOCK)
        print('Conexão vindo de:', addr)
        server.usuario = ""

        while True:
            dados = con.recv(1024)
            if not dados:
                break

            msg = stockmarket_pb2.MsgComando()
            msg.ParseFromString(dados)
            print("dados:", msg)
            msg_aut = stockmarket_pb2.MsgResp()

            if msg.HasField('autenticacao') and not msg.HasField('compra') and not msg.HasField('venda'):
                login = server.search(msg.autenticacao.usuario, msg.autenticacao.senha)
                print("login:",login)
                msg_aut = stockmarket_pb2.MsgResp()
                if login:
                    server.conectado = True
                    server.usuario = msg.autenticacao.usuario
                    msg_aut.status = 1
                else:
                    print("aqui")
                    msg_aut.status = 0
                con.send(msg_aut.SerializeToString())
            if msg.HasField('compra') and server.conectado == True:
                print("aqui compra")
                o_comp=Ordem(ativo=msg.compra.ativo,preco=msg.compra.oferta.preco,num=msg.compra.oferta.quantidade,usuario=server.usuario,compra=True)
                r_comp=s.lanca_ordem(o_comp)
                if r_comp:
                    for i in range(len(r_comp)):
                        if r_comp[i].compra == True:
                            msg_neg_compra = stockmarket_pb2.MsgResp()
                            msg_neg_compra.status = 2
                            msg_neg_compra.notificacao.exec.ativo = r_comp[i].ativo
                            msg_neg_compra.notificacao.exec.preco = r_comp[i].preco
                            msg_neg_compra.notificacao.exec.quantidade = r_comp[i].num
                            msg_neg_compra.notificacao.exec.tipo = 1
                            con.send(msg_neg_compra.SerializeToString())
            if msg.HasField('venda') and server.conectado == True:
                print("aqui venda")
                o_vend = Ordem(ativo=msg.venda.ativo,preco=msg.venda.oferta.preco,num=msg.venda.oferta.quantidade,usuario=server.usuario,compra=False)
                r_vend = s.lanca_ordem(o_vend)
                if r_vend:
                    for i in range(len(r_vend)):
                        if r_vend[i].compra == False:
                            msg_neg_venda = stockmarket_pb2.MsgResp()
                            msg_neg_venda.status = 2
                            msg_neg_venda.exec.ativo = r_vend[i].ativo
                            msg_neg_venda.exec.preco = r_vend[i].preco
                            msg_neg_venda.exec.quantidade = r_vend[i].num
                            msg_neg_venda.exec.tipo = 2
                            con.send(msg_neg_venda.SerializeToString())
            if msg.HasField('info') and server.conectado == True:
                ativo_not = msg.info.ativo
                notificar = msg.info.notificacao
            if msg.HasField('cancelar_compra') and server.conectado == True:
                o_can_comp = Ordem(ativo=msg.cancelar_compra.ativo,preco=msg.cancelar_compra.oferta.preco,num=msg.cancelar_compra.oferta.quantidade,usuario=server.usuario,compra=True)
                r_can_comp = s.cancela(o_can_comp)
            if msg.HasField('cancelar_venda') and server.conectado == True:
                o_can_vend = Ordem(ativo=msg.cancelar_venda.ativo,preco=msg.cancelar_venda.oferta.preco,num=msg.cancelar_venda.oferta.quantidade,usuario=server.usuario,compra=False)
                r_can_vend = s.cancela(o_can_vend)

        con.shutdown(SHUT_RDWR)