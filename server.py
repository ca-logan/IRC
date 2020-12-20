import socket
import sys
import select	#<-- use this library for dealing with socket.recv() requests as otherwise the server will idle and eat too much processing power

#Currently does not terminate properly when using a terminal keyboard interrupt
#IRC regexp for nicks is apparently: /\A[a-z_\-\[\]\\^{}|`][a-z0-9_\-\[\]\\^{}|`]*\z/i
#From IRC documentation: server names are limited to 63 characters
						#nicknames have a maximum length of 9 characters ('but clients should accept longer strings'???)
						#channel names are limited to 50 characters and must begin with # & + or ! and cannot include spaces, ctrl+G, or commas

IP = 'fc00:1337::17'	#IP/port info
PORT = 6667

class Client:
	###Some stuff about regexp here?

	def __init__(self, server, socket):
		self.server = server
		self.socket = socket
		self.nickname = b""
		self.realname = b""
		self.readbuffer = b""
		self.writebuffer = b""

	def write_buffer_size(self):	#skeleton
		return

	def parse_read_buffer(self):	#skeleton
		return

	def register_client(self, nickname):
		self.server = server
		self.nickname = nickname #need to then update this to server

	def broadcast_names(self):		#skeleton
		return

	def command_handler(self, command: bytes, arg: bytes):	##### THIS should probably be the bulk of the code
		if command == "NICK":
			register_client(arg)
		elif command == "JOIN":
			#join a channel with #name format
			return

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
		
		self.clients = {socket.socket: Client}	#dictionary storing client information [socket, user info] - not sure about this
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
				(clientsocket, address) = self.serversocket.accept()
				print(f"Connection established from {address[0]}/{address[1]}")
				self.clients[clientsocket] = Client(self, clientsocket)
				#clientsocket.recv(MAX_LENGTH)
				#clientsocket.send(bytes("Welcome to our IRC server!", "utf-8"))
			except KeyboardInterrupt:
				print(f"\nKeyboard interrupt detected. Goodbye.")
				sys.exit(1)

def main():
	server = Server(IP, PORT)
	server.start()

if __name__ == '__main__':
	main()