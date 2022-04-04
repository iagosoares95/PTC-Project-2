import sys
from socket import *
import stockmarket_pb2
from poller import Callback,Poller

class CbSocket(Callback):
    def __init__(self, sock, cli):
        self.sock = sock
        Callback.__init__(self, sock)
        self.cli = cli
        self.cli.autenticacao()

    def handle(self, poller_obj):
        msg = self.fd.recv(1024)
        self.cli.recebe(msg)

class CbKeyboard(Callback):
    def __init__(self, kb, cli):
        self.cli = cli
        Callback.__init__(self, kb)

    def handle(self, poller_obj):
        msg = self.fd.readline()
        self.cli.actions(msg)

class Cliente:
    def __init__(self, sock):
        self.soc = sock
        self.conectado = False

    def autenticacao(self):
        user = input('Por favor, insira seu usuário:\n')
        passwd = input('Senha:\n')
        aut = stockmarket_pb2.MsgComando()
        aut.autenticacao.usuario = user
        aut.autenticacao.senha = passwd
        self.soc.send(aut.SerializeToString())

    def recebe(self, dados):
        msg = stockmarket_pb2.MsgResp()
        msg.ParseFromString(dados)
        print("\nRecebido:",msg)
        if msg.status == 1:
            self.conectado = True
            print("Logado com sucesso.")
        if msg.status == 0:
            print("Credenciais erradas.")
            self.autenticacao()
        if self.conectado:
            if msg.status == 2:
                print("Ordem criada com sucesso!")
            if msg.status == 3:
                if msg.exec.tipo == 1:
                    print(f"Compra de {msg.exec.quantidade} {msg.exec.ativo} realizada com sucesso, ao preço de {msg.exec.preco}!")
                if msg.exec.tipo == 2:
                    print(f"Venda de {msg.exec.quantidade} {msg.exec.ativo} realizada com sucesso, ao preço de {msg.exec.preco}!")
            if msg.status == 4:
                print("Notificação ativada")
            if msg.status == 5:
                print("Notificação desativada")
            if msg.status == 6:
                print("Ordem de compra cancelada")
            if msg.status == 7:
                print("Ordem de venda cancelada")
            if msg.status == 8:
                print(f"{msg.info.ativo}: \n Último preço: {msg.info.ultimo_preco} \n Ordens de compra: {msg.info.compras} \n Ordens de venda: {msg.info.vendas}")
            if msg.status == 9:
                print("Conexão terminada")
                self.soc.close()
                sys.exit(0)
            self.menu()

    def termina(self):
        msg_saida = stockmarket_pb2.MsgComando()
        msg_saida.saida = True
        self.soc.send(msg_saida.SerializeToString())

    def info(self):
        msg_info = stockmarket_pb2.MsgComando()
        option = input('Ativar notificações de ativos? 1-Sim 2 -Não\n')
        if option == '1':
            msg_info.info.notificar = True
            acao = input('Qual ação deseja receber notificações?\n')
            msg_info.info.ativo = acao
            self.soc.send(msg_info.SerializeToString())
        if option == '2':
            msg_info.info.notificar = False
        
    def cancelar_oc(self):
        option = input('Qual ativo desejas cancelar a ordem?\n')
        msg_quant = input('Quantas ações deseja cancelar?\n')
        #Avisar q tem q ser numeros
        msg_preco = input('Por qual preço a ordem foi lançada?\n')
        msg_cancel_compra = stockmarket_pb2.MsgComando()
        msg_cancel_compra.cancela_compra.oferta.quantidade = int(msg_quant)
        msg_cancel_compra.cancela_compra.oferta.preco = int(msg_preco)
        msg_cancel_compra.cancela_compra.ativo = option
        self.soc.send(msg_cancel_compra.SerializeToString())
    
    def cancelar_ov(self):
        option = input('Qual ativo desejas cancelar a ordem?\n')
        msg_quant = input('Quantas ações deseja cancelar?\n')
        #Avisar q tem q ser numeros
        msg_preco = input('Por qual preço a ordem foi lançada?\n')
        msg_cancel_vend = stockmarket_pb2.MsgComando()
        msg_cancel_vend.cancela_venda.oferta.quantidade = int(msg_quant)
        msg_cancel_vend.cancela_venda.oferta.preco = int(msg_preco)
        msg_cancel_vend.cancela_venda.ativo = option
        self.soc.send(msg_cancel_vend.SerializeToString())

    def actions(self, msg):
        if int(msg) == 1:
            self.compra_acao()
        if int(msg) == 2:
            self.venda_acao()
        if int(msg) == 3:
            self.info()
        if int(msg) == 4:
            self.cancelar_oc()        
        if int(msg) == 5:
            self.cancelar_ov()
        if int(msg) == 6:
            self.termina()
        #else
    
    def menu(self):
            print('\nQuais opções abaixo deseja executar\n 1- Comprar ações\n 2- Vender ações\n 3- Notificações de preço\n 4- Cancelar ordem de compra\n 5- Cancelar ordem de venda\n 6- Sair\n')
    #tratar quando colocam letras

    def compra_acao(self):
        msg_nome = input('Qual nome da ação deseja comprar?\n')
        msg_quant = input('Quantas ações deseja comprar?\n')
        #Avisar q tem q ser numeros
        msg_preco = input('Por qual preço deseja comprar?\n')
        msg_compra = stockmarket_pb2.MsgComando()
        msg_compra.compra.ativo = msg_nome
        msg_compra.compra.oferta.quantidade = int(msg_quant)
        msg_compra.compra.oferta.preco = int(msg_preco)
        self.soc.send(msg_compra.SerializeToString())
    
    def venda_acao(self):
        msg_nome = input('Qual nome da ação deseja vender?\n')
        msg_quant = input('Quantas ações deseja vender?\n')
        msg_preco = input('Por qual preço deseja vender?\n')
        msg_venda = stockmarket_pb2.MsgComando()
        msg_venda.venda.ativo = msg_nome
        msg_venda.venda.oferta.quantidade = int(msg_quant)
        msg_venda.venda.oferta.preco = int(msg_preco)
        self.soc.send(msg_venda.SerializeToString())

if __name__ == '__main__': 
    print("Bem vindo a Corretora")
    client = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
    client.bind(('0.0.0.0', 0))
    client.connect(('0.0.0.0', 5556))
    cli = Cliente(client)
    cbsck = CbSocket(client, cli)
    cbkb = CbKeyboard(sys.stdin, cli)
    sched = Poller()
    sched.adiciona(cbsck)
    sched.adiciona(cbkb)
    sched.despache()