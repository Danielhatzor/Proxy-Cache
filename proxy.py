# -*- coding: utf-8 -*-
import socketserver
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import os
import requests
import json

# import time, json, regex

# Server stuff


hostName = "localhost"
serverPort = 8000
cookie_str = "__sch_device_identifier=a70525dd3cb6459e0ad6db9fb49c6ee8; afterlogin_url=https%3A%2F%2Fmy.schooler.biz%2Fs%2F44864%2F12RulesForLife-5%2F1; __sch_session_identifier_b8aotWg9n8axo=8a29998412db309ffbf4e8d5d067a706; _tichnut_tv_session=Y1QvaEljWExRdGkrWlVUSG5mZGtQdUtUSDROcHpkZzdtYUc1OExXWFNoUkZPVXo3aW0vVGdCcjZCbUVlcjZpM1BTeC9udnBpNmhqcXZuUCs4NzQ3MWtLUWR3czR6V094VzRXcXJMeFVsQXN6L0plTzZSVTI4T3ltanFSNkw3anB0VmgwRkFsaDdzVVp4UkNEaVZtNUE0eGJGdk9XUUdkdE1TZVdvMWNPUytkKzdBT1ZDSVhobXhpQjZWbHdQM1NMRHBycHc4Wk90L2Y1ZEQxLzJnZTZMak0vYnU1QU5SM09UZVNxWU1ZWXE5THZQdEhWOGN0UE1xL2RESGM2SmFvS01wU0pQeElJRlNrZ0Zvb1AzODk0SVlwRXNrcms3bUVJS3ZiQ3BVQTh6TzErTWlVNGVFeWhZRlhNVUtjYVg4SHFZSWhjek9qSkxEWS9SOTd6MnhFOXRBPT0tLUVZS0NQbWlOa0NSZnM3cmJxSVBGWXc9PQ%3D%3D--c7a193e5bb29b79f6d0af68546c4f044f674eaa5"
cookie_list = cookie_str.split("; ")
cookies = {}
for cookie in cookie_list:
    cookie_tuple = cookie.split("=")
    cookies[cookie_tuple[0]] = cookie_tuple[1]
print(cookies)

backend_server_addr = "https://my.schooler.biz"
website_download_dir = "./website"
default_server_path = "/s/44864/bundles"

class MyServer(BaseHTTPRequestHandler):
    backend_session = None

    # def __init__(self, request: bytes, client_address: tuple[str, int], server: socketserver.BaseServer):
    #     super().__init__(request, client_address, server)
    #     self.init_session()

    def init_session(self):
        #self.protocol_version = "1.1"
        self.backend_session = requests.session()
        self.backend_session.verify = False

    def return_data_to_client(self, headers_dict, content, status_code):
        self.send_response(status_code)
        for key in headers_dict:
            if key != "Content-Length" and key != "Transfer-Encoding" and key != "Server" and key != "Date":
                # print(key)
                self.send_header(key, headers_dict[key])

        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if self.path == "/":
            path = website_download_dir + default_server_path
        else:
            path = website_download_dir + self.path
        path = path.split("?")[0]
        if os.path.exists(path) and os.path.exists(path + ".headers"):
            with open(path + ".headers", mode="r") as headers_file:
                headers_content = headers_file.read()
                headers_dict = json.loads(headers_content)
            with open(path, mode="rb") as local_file:
                content = local_file.read()
            self.return_data_to_client(headers_dict, content, 200)
            return


        if self.backend_session is None:
            self.init_session()

        retry = True
        headers = self.headers
        # headers.add_header("Cookie", cookie_str)

        while retry:
            try:
                self.backend_session.headers = headers
                # self.backend_session.headers["Cookie"] = cookie_str
                for cookie_key in cookies:
                    self.backend_session.cookies.set(cookie_key, cookies[cookie_key])

                print(backend_server_addr + self.path)
                r = self.backend_session.get(backend_server_addr + self.path)

                if r.status_code >= 400:
                    print(r.status_code, self.path)
                    raise Exception

                tmp_headers = r.headers.copy()
                #tmp_headers["Content-Length"] = str(len(r.content))
                #a = tmp_headers.pop("Content-Length")
                #a = tmp_headers.pop("Transfer-Encoding")

                #self.send_header("Content-Length", str(len(r.content)))




                # Save file and headers
                path_without_file = path.removesuffix(path.split("/")[-1])
                Path(path_without_file).mkdir(parents=True, exist_ok=True)
                with open(path, mode="wb") as downloaded_file:
                    downloaded_file.write(r.content)
                with open(path + ".headers", mode="w") as fh:
                    p = json.dumps(dict(tmp_headers))
                    fh.write(p)

                self.return_data_to_client(tmp_headers, r.content, r.status_code)


                retry = False
                print("passed")
            except requests.exceptions.ConnectionError:
                print("Connection error, retrying")
                self.init_session()

                retry = True
            # except BaseException as e:
            #     print("error: skipped", e)
            #     self.send_response(r.status_code)
            #     self.end_headers()
            #     retry = False


if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
