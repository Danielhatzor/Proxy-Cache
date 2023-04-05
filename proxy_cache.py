# -*- coding: utf-8 -*-
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import os
import requests
import json


class ProxyCache(BaseHTTPRequestHandler):
    def __init__(self, backend_server_addr, website_download_dir, default_server_path, cookie_str, *args, **kwargs):
        self.backend_server_addr = backend_server_addr
        self.website_download_dir = website_download_dir
        self.default_server_path = default_server_path
        self.backend_session = None

        # Generating cookie dictionary
        cookie_list = cookie_str.split("; ")
        self.cookies = {}
        for cookie in cookie_list:
            if cookie != "":
                cookie_tuple = cookie.split("=")
                self.cookies[cookie_tuple[0]] = cookie_tuple[1]

        super().__init__(*args, **kwargs)

    def init_session(self):
        self.backend_session = requests.session()
        self.backend_session.verify = False

    def return_data_to_client(self, headers_dict, content, status_code):
        self.send_response(status_code)
        for key in headers_dict:
            if key != "Content-Length" and key != "Transfer-Encoding" and key != "Server" and key != "Date":
                self.send_header(key, headers_dict[key])

        self.end_headers()
        if content:
            self.wfile.write(content)

    def do_GET(self):
        tmp_path = self.path.split("?")[0]
        if tmp_path == "/":
            path = self.website_download_dir + self.default_server_path
        else:
            path = self.website_download_dir + self.path
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

        while retry:
            try:
                self.backend_session.headers = headers
                for cookie_key in self.cookies:
                    self.backend_session.cookies.set(cookie_key, self.cookies[cookie_key])

                print(self.backend_server_addr + self.path)
                r = self.backend_session.get(self.backend_server_addr + self.path)

                if r.status_code >= 400:
                    print(r.status_code, self.path)
                    self.return_data_to_client({}, None, r.status_code)
                    # raise Exception

                tmp_headers = r.headers.copy()

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
            except requests.exceptions.ConnectionError:
                print("Connection error, retrying")
                self.init_session()

                retry = True


if __name__ == "__main__":
    backend_server_addr = "https://www.google.com"
    website_download_dir = "./google"
    default_server_path = "/index.html"
    hostName = "localhost"
    serverPort = 8000
    cookie_str = "__sch_device_identifier=a70525dd3cb6459e0ad6db9fb49c6ee8; afterlogin_url=https%3A%2F%2Fmy.schooler." \
                 "biz%2Fs%2F44864%2F12RulesForLife-5%2F1; __sch_session_identifier_b8aotWg9n8axo=8a29998412db309ffbf4" \
                 "e8d5d067a706; _tichnut_tv_session=Y1QvaEljWExRdGkrWlVUSG5mZGtQdUtUSDROcHpkZzdtYUc1OExXWFNoUkZPVXo3a" \
                 "W0vVGdCcjZCbUVlcjZpM1BTeC9udnBpNmhqcXZuUCs4NzQ3MWtLUWR3czR6V094VzRXcXJMeFVsQXN6L0plTzZSVTI4T3ltanFS" \
                 "Nkw3anB0VmgwRkFsaDdzVVp4UkNEaVZtNUE0eGJGdk9XUUdkdE1TZVdvMWNPUytkKzdBT1ZDSVhobXhpQjZWbHdQM1NMRHBycHc" \
                 "4Wk90L2Y1ZEQxLzJnZTZMak0vYnU1QU5SM09UZVNxWU1ZWXE5THZQdEhWOGN0UE1xL2RESGM2SmFvS01wU0pQeElJRlNrZ0Zvb1" \
                 "AzODk0SVlwRXNrcms3bUVJS3ZiQ3BVQTh6TzErTWlVNGVFeWhZRlhNVUtjYVg4SHFZSWhjek9qSkxEWS9SOTd6MnhFOXRBPT0tL" \
                 "UVZS0NQbWlOa0NSZnM3cmJxSVBGWXc9PQ%3D%3D--c7a193e5bb29b79f6d0af68546c4f044f674eaa5"
    cookie_str = "1P_JAR=2023-04-05-04; AEC=AUEFqZdNEGQutJraQLYE2WzIXDq1yHCbNb4ROQ5SdVfzjFFhK2iYET-Di8U; NID=511=LE7Kr2U3v4xBuRHB04j7cFf6uDmBOZHFi_D6oTOSOIqNEr3vZBsj6icqCbXfQEudEfnHlkYibil9S_3gwwRM_eOQz9k71ODXNvoav6fcBGErKdPoY-HEhqiYKlOZxC4odGBZAULtpOMn-taV5iF7ZqhBdvESpou72z6m2ObbX9GJsIki4vElrWBEnCtfTevqFQZVfr-c-_tYpq1Rpc1InqQmjkU2Kbk7zuEdE9cbl1qG0DeGKJtf9gKs3b6rdPqsgLgjXf2pRnTXAJnh5aILY1UkWnU7iZbJXHjvxLjQf-8gR5Wp9m1hufcWuRuRi4zVf-uR0PA7yi96rltUgdTJQK2eHwXEeqU1ffac8rIdMhUFloCSUZRA1g; ANID=AHWqTUmGjC9Cylv6VW2RWS3rKX7YLd8pp9ScNnzWT3k3Hmc3StQV4WHWbic9wbVo; SID=UgjFFSbaPogDcB-QcRFKMsGBKsY7xVd8J-8uJtsLaisvWCd8jQaDvSQjOlYmBMTGVnpScA.; __Secure-1PSID=UgjFFSbaPogDcB-QcRFKMsGBKsY7xVd8J-8uJtsLaisvWCd8Z9HZ9DCOPGn0k2Sjt76MQQ.; __Secure-3PSID=UgjFFSbaPogDcB-QcRFKMsGBKsY7xVd8J-8uJtsLaisvWCd8c6oO9H205uAbHg1yiEdZIQ.; HSID=AG0xuOXRUVNkaHwYd; SSID=A5fKRp9n4lSgBm4Uu; APISID=DSkTCtQW92KowK6y/A-zSbFimByX5WHSDK; SAPISID=zaIKM31LmrJvwAKI/AbUbxy7ErD9qnkz7a; __Secure-1PAPISID=zaIKM31LmrJvwAKI/AbUbxy7ErD9qnkz7a; __Secure-3PAPISID=zaIKM31LmrJvwAKI/AbUbxy7ErD9qnkz7a; SIDCC=AFvIBn8LMDA2W3l3OurFEHlAh1ZIu-yg9U8R0VYzFP_CefcJZixblapu8fi9DVM-pHEtHQ5iKg; __Secure-1PSIDCC=AFvIBn9RormyRkX480ZYvXEItpNv0-P7kNp4_ZqCmZJUO2vgaFpo-cqtXjoSdzOImkUNRxb6cQ; __Secure-3PSIDCC=AFvIBn_f4eTh3yXWAzgkW_9VGOVmfpiseXifjL0DumGR3ofYlhHNL0fK0WH1Feq67JL5VqhVvF0; SEARCH_SAMESITE=CgQI-5cB; OTZ=6949238_48_48_120960_44_365700; UULE=a+cm9sZTogMQpwcm9kdWNlcjogMTIKdGltZXN0YW1wOiAxNjgwNjUxNTI5NjYzMDAwCmxhdGxuZyB7CiAgbGF0aXR1ZGVfZTc6IDMyMDc2MTQ0NwogIGxvbmdpdHVkZV9lNzogMzQ4MDYyNDcyCn0KcmFkaXVzOiAxMTA4NC45OApwcm92ZW5hbmNlOiA2Cg==; OGPC=19031986-1:"
    def proxy_cache_init(*args, **kwargs):
        return ProxyCache(backend_server_addr, website_download_dir, default_server_path, cookie_str,
                          *args, **kwargs)

    webServer = HTTPServer((hostName, serverPort), proxy_cache_init)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
