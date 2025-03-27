import socket

# since dns default operates on port 53
port = 53

# self hosted ip address
ip = "127.0.0.1"

# using IPV_4 and UDP instead of TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((ip, port))

# inifite loop listener
while True:
    # receive info with a byte limit
    data, address = sock.recvfrom(512)
    print(data)