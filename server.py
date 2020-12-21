import re
import socket
import sys
import select	

from typing import List

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

		self.host, self.port, _, _ = socket.getpeername() #ipv4: host, port = socket.getpeername()
		self.host = self.host.encode()

		self.readbuffer = b""
		self.writebuffer = b""
    	self.registered = False

	def parse_read_buffer(self):	#skeleton
		return
  
	def get_prefix(self):
		return b"%s!%s@%s" % (self.nickname, self.username, self.host)

	def writebuffer_size(self):
		return len(self.writebuffer)

	def message(self, msg: bytes):
		self.writebuffer += msg + b"\r\n"

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
				self.server.change_client_nickname(self)
				self.registered = True
				self.reply(b"001 %s :Welcome to our IRC server!" % self.nickname)
				self.reply(b"002 %s :Your host is %s" % (self.nickname, self.server.name))
				self.reply(b"003 %s :This server was created sometime" % self.nickname)
				self.reply(b"004 %s :SERVER INFO" % self.nickname)

	def nick_handler(self, args: bytes):
		args = args.split(b" ")
		if len(args) < 1:
			print("error - nick not given")
			return
		self.register_client(args[0])

	def join_handler(self, args: bytes):
		args = args.split(b" ")
		if len(args) < 1:
			print("error - channel name not given")
			return
		channelname = args[0]
		channel = self.server.get_channel(channelname)
		channel.add_client(self)
		message = b":%s JOIN %s" % (self.get_prefix(), channelname)
		self.message_channel(channel, message, True) # True - optional arg to notify that it's JOIN
		self.send_user_list(channel)
		
	def privmsg_handler(self, args: bytes):
		args = args.split(b" ", 1)
		if len(args) == 0:
			print("recipient not given")
			return
		if len(args) == 1:
			print("message not given")
			return
		if not args[1].startswith(b":"):
			print("message should start with ':'")
			return
		recipient = args[0]
		message = args[1][1:]
		message_to_send = b":%s PRIVMSG %s :%s" % (self.get_prefix(), recipient, message)
		client = self.server.get_client(recipient)
		if client:
			client.message(message_to_send)
			return
		channel = self.server.get_channel(recipient)
		if channel:
			self.message_channel(channel, message_to_send)
			return

	def command_handler(self, command: bytes, args: bytes):
		if not self.registered:
			self.register_handler(command, args)
			return
		if command == b"NICK":
			self.nick_handler(args)
			return
		elif command == b"JOIN":
			self.join_handler(args)
			return
		elif command == b"PRIVMSG":
			self.privmsg_handler(args)

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

	def write(self):
		sent = self.socket.send(self.writebuffer)
		self.writebuffer = self.writebuffer[sent:] # remove sent data from buffer

	def disconnect(self):
		self.socket.close()
		self.server.remove_client_from_server(self)

	def construct_message(self):	#skeleton
		return

	def reply(self, message):	#skeleton
		self.message(b":%s %s" % (self.server.name, message))

	def message_channel(self, channel, message, join = False):
		for client in channel.clientlist:
			if not join and client == self: # do not send if not join and this client
				continue
			client.message(message)

	def message_user(self, client):	#skeleton
		return

	def send_user_list(self, channel):
		user_list = b""
		for client in channel.clientlist:
			if not user_list:
				user_list += client.nickname
			else:
				user_list += b" " + client.nickname
		self.reply(b"353 %s = %s :%s" % (self.nickname, channel.channelname, user_list))
		self.reply(b"366 %s %s :End of NAMES list" % (self.nickname, channel.channelname))

class Channel:
	def __init__(self, server, channelname):
		self.server = server
		self.channelname = channelname
		self.clientlist = set()

	def add_client(self, client):
		self.clientlist.add(client)

	def remove_client(self, client):
		self.clientlist.remove(client)

class Server:
	def __init__(self, ip: str, port: int):
		self.ip = ip
		self.port = port
		self.name = socket.gethostname().encode()
		
		#self.clients = {socket.socket: Client}	#dictionary storing client information [socket, user info]
		self.clients = {}	#dictionary storing client information [socket, user info]
		
		self.nicks = {} # key - nickname
		self.channels = {} # key - channelname

	def has_channel(self, channel):
		return channel in self.channels

	def get_client(self, nickname):
		return self.nicks.get(nickname)

	def get_channel(self, channel):
		if self.has_channel(channel):
			return self.channels.get(channel)
		else:
			new_channel = Channel(self, channel) # add channel if does not exist
			self.channels[channel] = new_channel
			return self.channels[channel]

	def change_client_nickname(self, client, oldnick = False):
		if oldnick:
			del self.nicks[oldnick]
		self.nicks[client.nickname] = client	

	def remove_client_from_channel(self, client, channel_name):
		channel = self.channels[channel_name]
		channel.remove_client(client)

	def remove_client_from_server(self, client):
		del self.clients[client.socket]

	def remove_channel(self, channel):
		del self.channels[channel]

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
					self.clients[socket].write()
				
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