import multiprocessing
import math

class Telemetry(multiprocessing.Process):
    def __init__(self, serial_data_output: multiprocessing.Queue, telemetry_json_output: multiprocessing.Queue):
        super().__init__()
        self.serial_data_output = serial_data_output
        self.telemetry_json_output = telemetry_json_output

        print(self)
        self.run()

    def run(self):
        while True:
            while not self.serial_data_output.empty():
                test_passthrough_object = self.serial_data_output.get()
                # self.telemetry_json_output.put(test_passthrough_object)
                # print(f"Telemetry Passing SerDatOut->TelJson: {test_passthrough_object}")
                self.send_sample_websocket_json(test_passthrough_object)
                print(f"Telemetry sending sample websocket json")

    def send_sample_websocket_json(self, addAltitude):

        sample_json = {
            "version": "0.0.1",
            "org": "CU InSpace",
            "status": {
                "board": {
                    "connected": "yes"
                },
                "rocket": {
                    "call_sign": "Not a missile",
                    "status_code": 1,
                    "status_text": "ARMED"
                }
            },
            "telemetry_data": {
                "altitude_data": {
                    "altitude": {
                        "m": "400",
                        "ft": f"{1312 + addAltitude}"
                    },
                    "temperature": {
                        "celsius": f"{12 + math.floor(addAltitude/100)}",
                        "fahrenheit": "54"
                    }
                },
                "acceleration_data": {
                    "acceleration": {
                        "ms2": "40",
                        "ft2": "131"
                    }
                }
            }
        }

        self.telemetry_json_output.put(sample_json)
