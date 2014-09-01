# -*- coding: utf-8 -*-

# Simple HTTP file server that supports byte ranges

import SimpleHTTPServer, BaseHTTPServer
import os, re
import threading
from SocketServer import ThreadingMixIn
from utils import *


def HTTPRangeRequestHandler(file_for_path):
    class HTTPRangeRequestHandler_(SimpleHTTPServer.SimpleHTTPRequestHandler):
        range_pattern = re.compile(r"^bytes=(\d*)\-(\d*)$")
        protocol_version = "HTTP/1.1"

        def get_range(self, file_size):
            while True:
                print self.headers.getheader("Range")
                range = self.range_pattern.search(self.headers.getheader("Range") or "")
                if not range:
                    break

                # get ranges

                first = range.group(1)
                last = range.group(2)

                if first == "":
                    first = file_size - int(last)
                    if first < 0:
                        first = 0
                    size = file_size - first
                    if size <= 0: # !!! specs 14.35.1
                        break
                else:
                    first = int(first)
                    if last != "":
                        size = int(last) - first + 1
                        if size <= 0: # !!! specs 14.35.1
                            break
                    else:
                        size = file_size - first
                        if size <= 0: # !!! specs 14.35.1
                            break
                return first, size, True
            return 0, file_size, False

        @log_exception
        def do_HEAD(self):
            return self.do_GET(head=True)

        @log_exception
        def do_GET(self, head=False):
            Log.Info("GET")
            path = file_for_path(self.path)
            if not os.path.isfile(path):
                self.send_error(404, "File not found")
                return

            stat = os.stat(path)
            file_size = os.stat(path).st_size

            first, size, partial = self.get_range(os.stat(path).st_size)
            self.send_response(206 if partial else 200)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Last-Modified", self.date_time_string(stat.st_mtime))
            self.send_header("Content-type", self.guess_type(path))
            #self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Range", 'bytes ' + str(first) + '-' + str(first + size - 1) + '/' + str(file_size))
            self.send_header("Content-Length", size)
            self.end_headers()

            if head:
                return

            f = os.open(path, os.O_RDONLY)
            try:
                Log.Info("A")
                os.lseek(f, first, 0)
                Log.Info("B")
                while size > 0:
                    chunk = min(size, 4096)
                    Log.Info("C")
                    try:
                        self.wfile.write(os.read(f, chunk))
                    except:
                        break
                    size = size - chunk
            finally:
                os.close(f)
    return HTTPRangeRequestHandler_

class MultiThreadedHTTPServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass

@log_exception
def serve(port, file_for_path):
    Log.Info("Serve")
    httpd = MultiThreadedHTTPServer(('', port), HTTPRangeRequestHandler(file_for_path))
    httpd.serve_forever()

@log_exception
def launch(port, file_for_path):
    Log.Info("Launch")
    httpd = threading.Thread(target=serve, args=(port, file_for_path))
    httpd.start()
    return httpd

if __name__ == "__main__":
    launch(32499).join()