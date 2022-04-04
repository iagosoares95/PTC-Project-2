from socket import *
from server import Servidor
from enum import Enum
from poller import Callback,Poller,ExpiredHandlerError
import sys
from app_server import Sistema

class Estado(Enum):
  CONNECTED=1
  DISCONNECTED=0
  AUTH=2

class Server(Callback):
  '''O protocolo do lado servidor (está incompleto). Objetos Server
     não devem ser criados diretamente, e sim por meio de um objeto
     BaseServer'''

  def __init__(self, sock, sis):
    Callback.__init__(self, sock)
    self._sock = sock
    self.sis = sis
    self.srv = Servidor(self._sock, self.sis)

  def handle(self, poller_obj):
    '''trata uma mensagem recebida'''

    # recebe até 1024 bytes ... apenas um exemplo !
    msg = self._sock.recv(1024)
    if not msg: raise ExpiredHandlerError('finished')
    print(f'Server: recebeu {msg} do cliente {self._sock.getpeername()}')
    #msg = f'Recebido: {msg}'
    self.srv.recebe(msg)

class BaseServer(Callback):

  'Facilita receber conexões e instanciar o protocolo para tratá-las'

  def __init__(self, port:int):
    self._sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
    self._sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    self._sock.bind(('0.0.0.0', port))
    self._sock.listen(2)
    Callback.__init__(self, self._sock)
    self.sis = Sistema()

  def handle(self, poller_obj):
    '''Espera uma conexão de um cliente, criando então um 
     objeto Server para representá-la. Esse objeto Server é um Callback, 
     que é registrado no poller'''
    sock,addr = self._sock.accept()
    print('Conexão vindo de:', addr)
    poller_obj.adiciona(Server(sock, self.sis))

if __name__ == '__main__':
  server = BaseServer(5556)
  sched = Poller()
  sched.adiciona(server)
  sched.despache()
  sys.exit(0)