import re
import socket
import sys
import select	#<-- use this library for dealing with socket.recv() requests as otherwise the server will idle and eat too much processing power

from typing import List

#Currently does not terminate properly when using a terminal keyboard interrupt
#IRC regexp for nicks is apparently: /\A[a-z_\-\[\]\\^{}|`][a-z0-9_\-\[\]\\^{}|`]*\z/i
#From IRC documentation: server names are limited to 63 characters
						#nicknames have a maximum length of 9 characters ('but clients should accept longer strings'???)
						#channel names are limited to 50 characters and must begin with # & + or ! and cannot include spaces, ctrl+G, or commas

#IP = 'fc00:1337::17'	#IP/port info
IP = 'localhost'
PORT = 6667

class Client:
	lineseparator_regex = re.compile(rb"\r?\n") # regex is "\r\n" or "\n"
  
	def __init__(self, server, socket):
		self.server = server
		self.socket = socket
		self.nickname = b""
		self.username = b""
		self.realname = b""
		self.readbuffer = b""
		self.writebuffer = b""
    self.registered = False

	def parse_read_buffer(self):	#skeleton
		return

	def writebuffer_size(self):
		return len(self.writebuffer)

	def message(msg: bytes):
		self.writebuffer += msg

	def register_client(self, nickname):
		#self.server = server
		self.nickname = nickname #need to then update this to server
    
	def broadcast_names(self):		#skeleton
		return

	def register_handler(self, command: bytes, args: bytes):
		if self.nickname == b"":
			if command == b"NICK":
				self.nick_handler(args)
		elif self.realname == b"":
			if command == b"USER":
				args = args.split(b" ")
				if len(args) < 4:
					print("error - wrong args")
					return
				self.username = args[0]
				self.realname = args[3]
				self.registered = True

	def nick_handler(self, args: bytes):
		args = args.split(b" ")
		if len(args) < 1:
			print("error - nick not given")
			return
		self.register_client(args[0])

	def command_handler(self, command: bytes, args: bytes):
		print("command:")
		print(command)
		print("args:")
		print(args)
		if not self.registered:
			self.register_handler(command, args)
			return
		if command == b"NICK":
			self.nick_handler(args)
			return
		elif command == b"JOIN":
			#join a channel with #name format
			print("join channel")
			return
	
	def read(self, input: bytes):
		self.readbuffer = input
		lines = self.lineseparator_regex.split(self.readbuffer)
		for line in lines:
			if line != b"":
				split_line = line.split(b" ", 1)
				command = split_line[0]
				if len(split_line) == 1:
					args = []
				else:
					args = split_line[1]
				self.command_handler(command, args)

	def disconnect(self):	#skeleton
		return

	def construct_message(self):	#skeleton
		return

	def reply(self):	#skeleton
		return

	def message_channel(self, channel):	#skeleton
		return

	def message_user(self, client):	#skeleton
		return

	def send_user_list(self):	#skeleton
		return

class Channel:
	def __init__(self, server, channelname):
		self.server = server
		self.channelname = channelname
		self.clientlist = {socket.socket: Client}	###not sure about this dict

	def add_client(self, client):
		self.clientlist.add(client)

	def remove_client(self, client):
		self.clientlist.remove(client)

class Server:
	def __init__(self, ip: str, port: int):
		self.ip = ip
		self.port = port
		
		#self.clients = {socket.socket: Client}	#dictionary storing client information [socket, user info]
		self.clients = {}	#dictionary storing client information [socket, user info]
		self.clientList = list()

		self.nicks = {bytes, Client}
		self.channels = {bytes, Channel}

	def get_client(self, nickname):
		return self.nicks.get(nickname)

	def get_channel(self, channel):
		return self.channels.get(channel)

	def change_client_nickname(self, client, oldnick, newnick):	#skeleton
		return	

	def remove_client_from_channel(self, client, channel):	#skeleton
		return

	def remove_client_from_server(self, client):	#skeleton
		return

	def remove_channel(self, channel):	#skeleton
		return

	def start(self):
		self.serversocket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM) #create a new IPv4 streaming socket
		self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)	#allows the socket to reuse our server address	
		try:
			self.serversocket.bind((self.ip, self.port))	#bind the new socket to a public host with the conventional IRC port (6667)
		except socket.error as e:
			self.print(f"{e}: Could not bind to port {port}.")
			sys.exit(1)
		except OSError as o:
			self.print(f"{o}: Address already in use")
			sys.exit(1)
		self.serversocket.listen(5)	#the socket will listen for 5 requests at any time	
		print(f'Listening for incoming connections on {IP}/{PORT}')
		self.run()

	def run(self):
		while True:
			try:
				read_sockets, write_sockets, error_sockets = select.select([client.socket for client in self.clients.values()] + [self.serversocket],
					[
						client.socket for client in self.clients.values()
					if client.writebuffer_size() > 0
					],
					[], 10)

				for socket in read_sockets:
					if socket == self.serversocket:
						(clientsocket, address) = self.serversocket.accept()
						print(f"Connection established from {address[0]}/{address[1]}")
						self.clients[clientsocket] = Client(self, clientsocket)

					else: # client socket
						data = socket.recv(1024)
						self.clients[socket].read(data)

				for socket in write_sockets:
					sent = socket.send(self.clients[socket].writebuffer)
					print("write data:")
					print(sent)
				
				#(clientsocket, address) = self.serversocket.accept()
				#print(f"Connection established from {address[0]}/{address[1]}")
				#self.clients[clientsocket] = Client(self, clientsocket)

				#clientsocket.send(bytes("Welcome to our IRC server!", "utf-8"))
			except KeyboardInterrupt:
				print(f"\nKeyboard interrupt detected. Goodbye.")
				sys.exit(1)

def main():
	server = Server(IP, PORT)
	server.start()

if __name__ == '__main__':
	main()