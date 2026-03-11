import json


class ConfigManager:

    def __init__(self, path="config.json"):

        self.path = path

        with open(path) as f:
            self.config = json.load(f)

    def get_server(self):
        return self.config["server"]

    def get_tcp_ports(self):
        return self.config["tcp_ports"]

    def port_exists(self, port):

        for p in self.config["tcp_ports"]:
            if p["port"] == port:
                return True

        return False

    def add_printer(self, printer, port):

        if self.port_exists(port):
            raise ValueError("El puerto ya está asignado")

        self.config["tcp_ports"].append({
            "printer": printer,
            "port": port
        })
    
    def remove_printer(self, port):

        self.config["tcp_ports"] = [
            p for p in self.config["tcp_ports"]
            if p["port"] != port
        ]

    def set_https(self, enabled):

        self.config["server"]["https"] = enabled

    def set_host(self, host):

        self.config["server"]["host"] = host

    def save(self):

        with open(self.path, "w") as f:
            json.dump(self.config, f, indent=2)