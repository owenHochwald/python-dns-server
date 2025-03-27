import socket

# since dns default operates on port 53
port = 53

# self hosted ip address
ip = "127.0.0.1"
# ip = "8.8.8.8"

# using IPV_4 and UDP instead of TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((ip, port))


def build_response(data):
    
    # getting transaction id
    TransactionID = data[:2]
    TID = ''
    for byte in TransactionID:
        TID += hex(byte)[2:]  
        
    # get the flags
    Flags = get_flags(data[2:])      

# inifite loop listener
while True:
    # receive info with a byte limit
    data, address = sock.recvfrom(512)
    r = build_response(data)
    sock.sendto(r, address)