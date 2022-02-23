import sys
import attr
import datetime
from typing import List

@attr.s(eq=False)
class Ordem:
    '''Uma ordem, que pode ser de compra (default) ou venda.
    Os atributos são:
    @ativo: o nome do ativo
    @num: a quantidade que se deseja negociar
    @preco: o valor que se deseja para a negociacao
    @compra: informa se é compra (True) ou venda (False)
    @usuario: a identificacao do usuario que lançou a ordem (opcional)
    @negociada: a quantidade já negociada do ativo nesta ordem
    @total: o valor total negociado nesta ordem'''
    
    ativo=attr.ib(default='')
    num=attr.ib(default=0)
    preco=attr.ib(default=0)
    compra=attr.ib(default=True)
    usuario=attr.ib(default='')
    negociada=attr.ib(default=0)
    total=attr.ib(default=0)

    @property
    def executada(self)->bool:
      'Retorna True se a ordem foi completamente negociada'
      return self.negociada == self.num
      
    @property
    def unidades(self)->int:
      'Retorna quantas unidades desta ordem foram negociada até o momento'
      return self.num - self.negociada
      
@attr.s
class Ativo:
    '''Representa um Ativo que pode ser negociado.
    Seus atributos são:
    @nome: nome do ativo
    @compras: a lista de ordens de compra pendentes
    @vendas: a lista de ordens de venda pendentes
    @cotacao: o valor da última negociação realizada
    @data: a data e horário da última negociação realizada'''
    nome=attr.ib(default='')
    compras=attr.ib(factory=list)
    vendas=attr.ib(factory=list)
    cotacao=attr.ib(default=0)
    data=attr.ib(factory=datetime.datetime.now)

    def _obtem_lista(self, compra:bool):
        if compra:
          return self.compras
        else:
          return self.vendas

    def cria_ordem(self, ordem:Ordem):
        'Cria uma ordem, que deve estar descrita no objeto ordem'
        ordens = self._obtem_lista(ordem.compra)
        ordens.append(ordem)          
    
    def cancela(self, ordem:Ordem):
        'Cancela uma ordem, que deve estar descrita no objeto ordem'
        ordens = self._obtem_lista(ordem.compra)
        ordens.remove(ordem)       

    def cria_cotacao(self, ordem:Ordem):
      self.cotacao = ordem.preco
    
    def negocia(self)->List[Ordem]:
        '''Negocia as ordens de compra e venda de um ativo
        Retorna uma lista de ordens executadas, mesmo que parcialmente'''
        r = set()
        while self.vendas and self.compras:
            venda=min(self.vendas, key=lambda x: x.preco)
            compra=max(self.compras, key=lambda x: x.preco)
            if venda.preco <= compra.preco:
                qtde = min(venda.unidades, compra.unidades)
                venda.negociada += qtde
                compra.negociada += qtde
                venda.total += venda.preco*qtde
                compra.total += venda.preco*qtde
                self.cotacao = venda.preco
                self.data = datetime.datetime.now()
                r.add(venda)
                r.add(compra)
                if venda.executada:
                  self.vendas.remove(venda)
                if compra.executada:
                  self.compras.remove(compra)
            else:
                break
        return list(r)
        
@attr.s
class Sistema:
    '''Representa um sistema composto por um conjunto de ativos em negociação.
    Na prática, funciona como um container que ajuda a lançar e cancelar ordens,
    incluir ativos, e obter informações sobre um ativo'''
    ativos=attr.ib(factory=dict)
     
    def _obtem_ativo(self, ativo):
        if not ativo in self.ativos:
          self.ativos[ativo] = Ativo(ativo)
        return self.ativos[ativo]

    def cria_ativo(self, ordem:Ordem):
      obj = self._obtem_ativo(ordem.ativo)
      obj.cria_cotacao(ordem)
    
    def lanca_ordem(self, ordem:Ordem):
        '''Lança uma ordem de compra ou venda, descrita no objeto ordem
        Retorna uma lista com as ordens que foram negociadas, após a inclusão
        dessa nova ordem (caso existam)'''
        obj = self._obtem_ativo(ordem.ativo)
        obj.cria_ordem(ordem)
        return obj.negocia()
        
    def cancela(self, ordem:Ordem):
        'Cancela uma ordem, descrita no objeto ordem'
        if not ordem.ativo in self.ativos: raise ValueError('ativo desconhecido')
        self.ativos[ordem.ativo].cancela(ordem)
        
    def info(self, ativo:str)->Ativo:
        'Obtem informações sobre um ativo, na forma de um objeto Ativo'
        if not ativo in self.ativos: raise ValueError('ativo desconhecido')
        return self.ativos[ativo]



