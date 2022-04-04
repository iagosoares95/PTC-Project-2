from socket import *
import stockmarket_pb2
import poller
from dataclasses import dataclass
from app_server import Ordem

@dataclass
class Usuario:
    nome: str
    senha: str
    ativos_not: list
    conectado: bool

class Servidor():
    def __init__(self, con, sis):
        self.usuario = None
        self.s = sis
        self.database = {}
        self.database['Andrey'] = Usuario("Andrey","123","",False)
        self.database['Iago'] = Usuario("Iago","456","",False)
        self.database['Sobral'] = Usuario("Sobral","789","",False)
        self.con = con

    def search(self, msg):
        if msg in self.database:
            senha = self.database[msg].senha
            self.usuario = self.database[msg]
            return senha
        return False

    def autenticacao(self, msg):
        senha = self.search(msg.autenticacao.usuario)
        msg_aut = stockmarket_pb2.MsgResp()
        if senha == msg.autenticacao.senha:
            self.usuario.conectado = True
            msg_aut.status = 1
        else:
            msg_aut.status = 0
        self.con.send(msg_aut.SerializeToString())

    def notifica(self, ativo):
        if ativo in self.usuario.ativos_not:
            msg_not = stockmarket_pb2.MsgResp()
            ord = self.s.info(ativo)
            msg_not.status = 8
            msg_not.info.ativo = ativo
            msg_not.info.ultimo_preco = ord.cotacao
            if ord.compras:
                for i in range(len(ord.compras)):
                    msg_not.info.compras.add(quantidade=ord.compras[i].num, preco=ord.compras[i].preco)
            if ord.vendas:
                for j in range(len(ord.vendas)):
                    msg_not.info.vendas.add(quantidade=ord.vendas[i].num, preco=ord.vendas[i].preco)
            print("aqui:", msg_not)
            self.con.send(msg_not.SerializeToString())

    def venda(self, msg):
        o_vend = Ordem(ativo=msg.venda.ativo,preco=msg.venda.oferta.preco,num=msg.venda.oferta.quantidade,usuario=self.usuario.nome,compra=False)
        r_vend = self.s.lanca_ordem(o_vend)
        if(r_vend):
            for i in range(len(r_vend)):
                if r_vend[i].compra == False and r_vend[i].usuario == self.usuario.nome:
                    msg_neg_venda = stockmarket_pb2.MsgResp()
                    msg_neg_venda.status = 3
                    msg_neg_venda.exec.ativo = msg.venda.ativo
                    msg_neg_venda.exec.preco = msg.venda.oferta.preco
                    msg_neg_venda.exec.quantidade = msg.venda.oferta.quantidade
                    msg_neg_venda.exec.tipo = 2
                    self.con.send(msg_neg_venda.SerializeToString())
        else:
            new_msg_neg_venda = stockmarket_pb2.MsgResp()
            new_msg_neg_venda.status = 2
            self.con.send(new_msg_neg_venda.SerializeToString())
        self.notifica(msg.venda.ativo)

    def compra(self, msg):
       # s = Sistema()
        o_comp = Ordem(ativo=msg.compra.ativo, preco=msg.compra.oferta.preco, num=msg.compra.oferta.quantidade, usuario=self.usuario.nome, compra=True)
        r_comp = self.s.lanca_ordem(o_comp)
        if r_comp:
            for i in range(len(r_comp)):
                if r_comp[i].compra == True and r_comp[i].usuario == self.usuario.nome:
                    msg_neg_compra = stockmarket_pb2.MsgResp()
                    msg_neg_compra.status = 3
                    msg_neg_compra.exec.ativo = msg.compra.ativo
                    msg_neg_compra.exec.preco = msg.compra.oferta.preco
                    msg_neg_compra.exec.quantidade = msg.compra.oferta.quantidade
                    msg_neg_compra.exec.tipo = 1
                    self.con.send(msg_neg_compra.SerializeToString())
        else:
            new_msg_neg_compra = stockmarket_pb2.MsgResp()
            new_msg_neg_compra.status = 2
            self.con.send(new_msg_neg_compra.SerializeToString())
        self.notifica(msg.compra.ativo)

    def enable_info(self, msg):
        msg_en_not = stockmarket_pb2.MsgResp()
        if msg.info.notificar:
            msg_en_not.status = 4
            if self.s.info(msg.info.ativo):
                self.usuario.ativos_not+=msg.info.ativo
        else:
            self.usuario.ativos_not.remove(msg.info.ativo)
            msg_en_not.status = 5
        self.con.send(msg_en_not.SerializeToString())

    def cancela_comp(self,msg):
        cancel_ord_comp = Ordem(ativo=msg.cancela_compra.ativo, preco=msg.cancela_compra.oferta.preco, num=msg.cancela_compra.oferta.quantidade, usuario=self.usuario.nome, compra=True)
        self.s.cancela(cancel_ord_comp)
        msg_cancel_compra = stockmarket_pb2.MsgResp()
        msg_cancel_compra.status = 6
        self.con.send(msg_cancel_compra.SerializeToString())
        self.notifica(msg.cancela_compra.ativo)

    def cancela_vend(self,msg):
        cancel_ord_vend = Ordem(ativo=msg.cancela_venda.ativo, preco=msg.cancela_venda.oferta.preco, num=msg.cancela_venda.oferta.quantidade, usuario=self.usuario.nome, compra=False)
        self.s.cancela(cancel_ord_vend)
        msg_cancel_vend = stockmarket_pb2.MsgResp()
        msg_cancel_vend.status = 7
        self.con.send(msg_cancel_vend.SerializeToString())
        self.notifica(msg.cancela_venda.ativo)

    def termina(self, msg):
        self.usuario = None
        msg_fim = stockmarket_pb2.MsgResp()
        msg_fim.status = 9
        self.con.send(msg_fim.SerializeToString())

    def recebe(self, dados):
        msg = stockmarket_pb2.MsgComando()
        msg.ParseFromString(dados)
        print(msg)
        if msg.HasField('autenticacao') and not msg.HasField('compra') and not msg.HasField('venda'):
            self.autenticacao(msg)
        if msg.HasField('compra') and self.usuario.conectado:
            self.compra(msg)
        if msg.HasField('venda') and self.usuario.conectado:
            self.venda(msg)
        if msg.HasField('info') and self.usuario.conectado:
            self.enable_info(msg)
        if msg.HasField('saida') and self.usuario.conectado:
            self.termina(msg)
        if msg.HasField('cancela_compra') and self.usuario.conectado:
            self.cancela_comp(msg)
        if msg.HasField('cancela_venda') and self.usuario.conectado:
            self.cancela_vend(msg)