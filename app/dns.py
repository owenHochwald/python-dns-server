import socket

# since dns default operates on port 53
port = 53

# self hosted ip address
ip = "127.0.0.1"

# using IPV_4 and UDP instead of TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((ip, port))

def get_flags(flags):
    byte1 = bytes(flags[:1])
    byte2 = bytes(flags[1:2])
    
    rflags = ''
    
    QR = '1'
    
    # build opcode from first byte
    OPCODE = ''
    
    for bit in range(1,5):
        # convert byte to int with a bit shift
        # value of the current bit will increase for each iteration
        OPCODE += str(ord(byte1)&(1<<bit))
        
    AA = '1'
    # we will only be passing short messages
    TC = '0'
    RD = '0'
    # not supporting recursion
    RA = '0'
    Z = '000'
    # response code to always success
    RCODE = '0000'
    
    # forming the flags
    first = int(QR+OPCODE+AA+TC+RD, 2).to_bytes(1, byteorder='big')
    second = int(RA+Z+RCODE).to_bytes(1, byteorder='big')
    return first+second

def get_question_domain(data):
    state = 0 
    expected_length = 0
    domain_string = ''
    domain_parts = []
    x = 0
    y = 0
    
    for byte in data:
        if state == 1:
            domain_string += chr(byte)
            x += 1
            
            if x == expected_length:
                domain_parts.append(domain_string)
                domain_string = ''
                state = 0
                x = 0 
            if byte == 0:
                domain_parts.append(domain_string)
                break
            
        else:
            state = 1
            expected_length = byte
        
        x += 1
        y += 1
        
    question_type = data[y+1: y+3]

    return (domain_parts, question_type)


def build_response(data):
    
    # getting transaction id
    TransactionID = data[:2]
    TID = ''
    for byte in TransactionID:
        TID += hex(byte)[2:]  
    
        
    # get the flags
    Flags = get_flags(data[2:4])    
    
    # question count where we only support 1 question
    QDCOUNT = b'\x00\x01'
    
    # answer count
    get_question_domain(data[12:])

# inifite loop listener
while True:
    # receive info with a byte limit
    data, address = sock.recvfrom(512)
    r = build_response(data)
    sock.sendto(r, address)