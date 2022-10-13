import multiprocessing


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
                self.telemetry_json_output.put(test_passthrough_object)
                print(f"Telemetry Passing SerDatOut->TelJson: {test_passthrough_object}")



