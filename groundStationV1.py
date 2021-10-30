# Ground station software for communication with the CU-InSpace rocket via an 
# RN2483 LoRa radio module.
# Authors: 



def init_ground_station():
    """initialize the configurations for the ground station
        author: zack
        step 1: figure out all the commands we need to do (on paper)
        step 2: after write_to_ground_station is complete then write out code"""
        

    return 0


def write_to_ground_station(register:int):
    """writes data to the ground station via UART
       author: tarik, Fahim
       step 1: rudimentary write
       step 2: commands? 
       @param register:address of the register you want to write to"""
    return 0


def read_from_ground_station(register:int):
    """reads data from the ground station via UART and puts it into the 
       correct data format to be passed onto the UI (check the logging format)
       author: elias 
       @param  register: address of register to read from
       @return data: the data that is stored in that register
    """
    return 0

    
    
def load_map():
    """load in a map that can be used offline
        author: """
    return 0
