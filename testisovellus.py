import crc8
import socket
import random
import time

class VirtualSocket:
    def __init__(self, real_socket):
        self.real_socket = real_socket
        # Modify these values to simulate different errors in UDP data receival
        self.drop_probability = 0
        self.delay_probability = 0
        self.bit_error_probability = 0
        self.crc8 = crc8.crc8()
        self.sequence_number = 0

    def bit_error(self, data):
        index = random.randint(0, len(data) - 1)
        bit_position = 1 << random.randint(0, 7)
        data_with_error = bytearray(data)
        data_with_error[index] ^= bit_position
        print("Added a bit error to the packet data")
        return bytes(data_with_error)

    def verify_crc(self, data):
        # Check CRC before returning data
        checksum = data[-1]
        data_without_crc = data[:-1]

        self.crc8.update(data_without_crc)
        calculated_crc = self.crc8.digest()
        calculated_crc_int = int.from_bytes(calculated_crc, byteorder='big')

        if checksum != calculated_crc_int:
            print("CRC check failed. Data may be corrupted.")
            self.crc8.reset()
            return b''
        self.crc8.reset()
        return data

    def xor_checksum(self, data):
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum

    def sendto(self, data, address):
        ack_packet = f"ACK {self.sequence_number}".encode()
        self.sequence_number += 1
        print("The ACK has been sent")
        ack_packet += bytes([self.xor_checksum(ack_packet)])
        self.real_socket.sendto(ack_packet, address)

    def recvfrom(self, buffer_size):
        # Method for receiving data from the virtual socket
        data, address = self.real_socket.recvfrom(buffer_size)
        rand = random.uniform(0, 1)
        if rand <= self.drop_probability:
            # Simulate dropping the received packet
            print("Dropped received packet")
            return b'', address
        if rand <= self.delay_probability:
            # Simulate delaying the received packet
            delay = random.randint(1, 5)
            print(f"The packet has been delayed for {delay} seconds")
            time.sleep(delay)
        if rand <= self.bit_error_probability:
            # Simulate a byte having a single bit error    
            data = self.bit_error(data)
        data = self.verify_crc(data)
        
        return data, address
    
class TestiSov:
    def __init__(self):
        # Create a UDP socket and a VirtualSocket on it
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(('127.0.0.1', 6666))
        self.virtual_socket = VirtualSocket(udp_socket)

    def run(self):
        listening = True
        while listening:
            try:
                rec, addr = self.virtual_socket.recvfrom(256)
                print(rec.decode())
                self.virtual_socket.sendto(b'', addr)
            except socket.error as e:
                listening = False
                print("Caught an exception:", e)
                break

if __name__ == "__main__":
    test_sov = TestiSov()
    test_sov.run()
