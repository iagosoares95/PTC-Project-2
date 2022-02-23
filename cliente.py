import sys
from socket import *
import poller
import stockmarket_pb2

class CbSocket(poller.Callback):
    def __init__(self, sock):
        self.cli = Clientao(sock)
        poller.Callback.__init__(self, sock, 10)
        self.disable_timeout()

    def handle(self):
        msg = self.fd.recv(1024)
        self.cli.recebe(msg)

class CbStdin(poller.Callback):
    def __init__(self, sock):
        self.cli = Clientao(sock)
        poller.Callback.__init__(self, sys.stdin, 1)
        self.enable_timeout()
    
    def handle_timeout(self):
        self.disable_timeout()
        self.cli.autenticacao()

    def handle(self):
        msg = self.fd.readline()
        self.cli.actions(msg)

class Clientao:
    def __init__(self, sock):
        self.soc = sock
        self.conectado = False

    def recebe(self, data):
        msg = stockmarket_pb2.MsgResp()
        msg.ParseFromString(data)
        print("Recebido:",msg)
        if self.conectado == True:
            print('\nQuais opções abaixo deseja executar\n 1- Comprar ações\n 2- Vender ações\n 3- Notificações de preço\n 4- Cancelar ordem de compra\n 5- Cancelar ordem de venda\n 6- Sair\n')
        if msg.status == 1:
            self.conectado = True
            print("Logado com sucesso.")
            print('\nQuais opções abaixo deseja executar\n 1- Comprar ações\n 2- Vender ações\n 3- Notificações de preço\n 4- Cancelar ordem de compra\n 5- Cancelar ordem de venda\n 6- Sair\n')
        if msg.status == 0:
            print("Credenciais erradas.")
            self.autenticacao()
        if msg.status == 2:
            if msg.exec.tipo == 1:
                print("Compra realizada co sucesso!")
            if msg.exec.tipo == 2:
                print("Venda realizada com sucesso!")
            print("Ativo:", msg.exec.ativo)
            print("Quantidade:", msg.exec.quantidade)
            print("Preço:", msg.exec.preco)

    def compra_acao(self):
        msg_nome = input('Qual nome da ação deseja comprar?')
        msg_quant = input('Quantas ações deseja comprar?')
        msg_preco = input('Por qual preço deseja comprar?')
        msg = stockmarket_pb2.MsgComando()
        msg.compra.ativo = msg_nome
        msg.compra.oferta.quantidade = int(msg_quant) #float(
        msg.compra.oferta.preco = int(msg_preco)
        #print("mensagem:", msg)
        self.soc.send(msg.SerializeToString())
        print('\nQuais opções abaixo deseja executar\n 1- Comprar ações\n 2- Vender ações\n 3- Notificações de preço\n 4- Cancelar ordem de compra\n 5- Cancelar ordem de venda\n 6- Sair\n')

    def vende_acao(self):
        msg_nome = input('Qual nome da ação deseja vender?')
        msg_quant = input('Quantas ações deseja vender?')
        msg_preco = input('Por qual preço deseja vender?')
        msg = stockmarket_pb2.MsgComando()
        msg.venda.ativo = msg_nome
        msg.venda.oferta.quantidade = int(msg_quant) #float(
        msg.venda.oferta.preco = int(msg_preco)
        #print("mensagem:", msg)
        self.soc.send(msg.SerializeToString())
        print('\nQuais opções abaixo deseja executar\n 1- Comprar ações\n 2- Vender ações\n 3- Notificações de preço\n 4- Cancelar ordem de compra\n 5- Cancelar ordem de venda\n 6- Sair\n')

    def info(self):
        msg_info = stockmarket_pb2.MsgComando()
        opc = input('Deseja ativar notificações de ativos? 1-Sim 2-Não')
        if opc == '1':
            msg_info.info.notificacao = True
            acao = input('Qual ação deseja receber notificações?')
        if opc =='2':
            msg_info.info.notificacao = False
        msg_info.info.ativo = acao
        self.soc.send(msg_info.SerializeToString())
        print('\nQuais opções abaixo deseja executar\n 1- Comprar ações\n 2- Vender ações\n 3- Notificações de preço\n 4- Cancelar ordem de compra\n 5- Cancelar ordem de venda\n 6- Sair\n')

    def cancela_compra(self):
        msg_can_compra = stockmarket_pb2.MsgComando()
        can_compra = input('De que ação deseja cancelar a ordem de compra?')
        msg_quant = input('Quantidade de ações definida na ordem:')
        msg_preco = input('Preço dado na ordem:')
        msg_can_compra.cancelar_compra.ativo = can_compra
        msg_can_compra.cancelar_compra.oferta.quantidade = int(msg_quant) #float(
        msg_can_compra.cancelar_compra.oferta.preco = int(msg_preco)
        self.soc.send(msg_can_compra.SerializeToString())
        print('\nQuais opções abaixo deseja executar\n 1- Comprar ações\n 2- Vender ações\n 3- Notificações de preço\n 4- Cancelar ordem de compra\n 5- Cancelar ordem de venda\n 6- Sair\n')

    def cancela_venda(self):
        msg_can_venda = stockmarket_pb2.MsgComando()
        can_venda = input('De que ação deseja cancelar a ordem de venda?')
        msg_quant = input('Quantidade de ações definida na ordem:')
        msg_preco = input('Preço dado na ordem:')
        msg_can_venda.cancelar_venda.ativo = can_venda
        msg_can_venda.cancelar_venda.oferta.quantidade = int(msg_quant) #float(
        msg_can_venda.cancelar_venda.oferta.preco = int(msg_preco)
        self.soc.send(msg_can_venda.SerializeToString())
        print('\nQuais opções abaixo deseja executar\n 1- Comprar ações\n 2- Vender ações\n 3- Notificações de preço\n 4- Cancelar ordem de compra\n 5- Cancelar ordem de venda\n 6- Sair\n')

    def actions(self, msg):
        if int(msg) == 1:
            self.compra_acao() 
        if int(msg) == 2:
            self.vende_acao()
        if int(msg) == 3:
            self.info()
        if int(msg) == 4:
            self.cancela_compra()
        if int(msg) == 5:
            self.cancela_venda()

    def autenticacao(self):
        user = input('Por favor, insira seu usuário:\n')
        passwd = input('Senha:\n')
        aut = stockmarket_pb2.MsgComando()
        aut.autenticacao.usuario = user
        aut.autenticacao.senha = passwd
        self.soc.send(aut.SerializeToString())

if __name__ == '__main__': 
    print("Bem vindo a Corretora")
    client = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
    client.bind(('0.0.0.0', 0))
    client.connect(('0.0.0.0', 5000))
    cli = Clientao(client)
    cb_sock = CbSocket(client)
    cb_inp = CbStdin(client)
    sched = poller.Poller()
    sched.adiciona(cb_sock)
    sched.adiciona(cb_inp)
    sched.despache()