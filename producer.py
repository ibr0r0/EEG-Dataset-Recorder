# THIS IS FOR TESTING, NOT WORKING PERFECTLY 


import time
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds

BoardShim.enable_dev_board_logger()

SERIAL_PORT = "/dev/tty.usbserial-XXXX"  
MULTICAST_IP = "225.1.1.1"             
PORT = 6677

params = BrainFlowInputParams()
params.serial_port = SERIAL_PORT

board_id = BoardIds.CYTON_BOARD.value   
board = BoardShim(board_id, params)
board.prepare_session()

board.add_streamer(f"streaming_board://{MULTICAST_IP}:{PORT}")

board.start_stream()
print(f"Producing BrainFlow stream at {MULTICAST_IP}:{PORT} from Cyton...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    board.stop_stream()
    board.release_session()
