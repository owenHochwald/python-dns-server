import socket
import glob
import json
# since dns default operates on port 53
port = 53

# self hosted ip address
ip = "127.0.0.1"

# using IPV_4 and UDP instead of TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((ip, port))



def load_zones():
    
    json_zone = {}
    zone_files = glob.glob('zones/*.zone')
    
    # loading into our program
    for zone in zone_files:
        with open(zone) as zone_data:
            data = json.load(zone_data)
            zone_name = data["$origin"]
            json_zone[zone_name] = data
    
    
zone_data = load_zones()


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
            if byte != 0:
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
        
        y += 1
        
    question_type = data[y: y+2]

    return (domain_parts, question_type)


def get_zone(domain):
    global zone_data
    
    # joining the lists
    zone_name = '.'.join(domain) + "."
    return zone_data[zone_name]
    

def get_recs(data):
    domain, question_type = get_question_domain(data)
    qt = ''
    if question_type == b'\x00\x01':
        qt = 'a'
    
    zone = get_zone(domain)
    
    # return relevant records
    return (zone[qt], qt, domain)

def build_question(domain_name, rec_type):
    # convert parameters to bytes
    qbytes = b''
    
    for part in domain_name:
        length = len(part)
        qbytes += bytes([length])
        
        # show chars with the length preceding it
        for char in part:
            qbyts += ord(char).to_bytes(1, byteorder='big')

    # record type            
    if rec_type == 'a':
        qbytes += (1).to_bytes(2, byteorder='big')
        
    # to represent the internet class
    qbytes += (1).to_bytes(2, byteorder='big')
    return qbytes

def rec_to_bytes(domain_name, rec_type, recttl, recval):
    # doing simple compression
    rbytes = b'\xc0\x0c'
    
    if rec_type == 'a':
        rbytes = rbytes + bytes([0]) + bytes([1])
        
    rbytes = rbytes + bytes([0]) + bytes([1])
    
    #store ttl
    rbytes += int(recttl).to_bytes(4, byteorder='big')
    
    if rec_type == "a":
        rbytes = rbytes + bytes([0]) + bytes([4])
        
        for part in recval.split('.'):
            rbytes += bytes([int(part)])
            
    return rbytes
    


def build_response(data):
    
    # getting transaction id
    TransactionID = data[:2]
        
    # get the flags
    Flags = get_flags(data[2:4])    
    
    # question count where we only support 1 question
    QDCOUNT = b'\x00\x01'
    
    # answer count
    ANCOUNT = len(get_recs(data[12:])[0]).to_bytes(2, byteorder='big')

    # namserver count
    NSCOUNT = (0).to_bytes(2, byte='big')
    # additional section count
    ARCOUNT = (0).to_bytes(2, byte='big')
    
    dns_header = TransactionID+Flags+QDCOUNT+ANCOUNT+NSCOUNT+ARCOUNT
    
    dns_body = b''
    
    # start on 12th byte since dns record is 12 bytes long
    records, rec_type, domain_name = get_recs(data[12:])
    
    dns_question = build_question(domain_name, rec_type)
    
    for record in records:
        dns_body += rec_to_bytes(domain_name, rec_type, record['ttl'], record['value'])
    
    return dns_header + dns_question + dns_body
    
# inifite loop listener
while True:
    # receive info with a byte limit
    data, address = sock.recvfrom(512)
    r = build_response(data)
    sock.sendto(r, address)