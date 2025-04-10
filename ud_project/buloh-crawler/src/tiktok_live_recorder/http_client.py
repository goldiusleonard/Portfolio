import requests


class HttpClient:
    def __init__(self, proxy=None, cookies=None):
        """
        Initializes the HTTP client with optional proxy and cookies.
        """
        self.req = None
        self.proxy = proxy
        self.cookies = cookies
        self.configure_session()

    def configure_session(self) -> None:
        """
        Configures the HTTP session with headers and cookies.
        """
        self.req = requests.Session()
        self.req.headers.update(
            {
                "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Linux"',
                "Accept-Language": "en-US",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.6478.127 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "image/avif,image/webp,image/apng,*/*;q=0.8,"
                    "application/signed-exchange;v=b3;q=0.7"
                ),
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-User": "?1",
                "Sec-Fetch-Dest": "document",
                "Priority": "u=0, i",
                "Referer": "https://www.tiktok.com/",
            }
        )

        if self.cookies is not None:
            self.req.cookies.update(self.cookies)

        self.check_proxy()

    def check_proxy(self) -> None:
        """
        Checks if the proxy is valid and updates the session with the proxy.
        """
        if self.proxy is None:
            return

        print(f"Testing proxy: {self.proxy}...")
        proxies = {"http": self.proxy, "https": self.proxy}

        try:
            response = requests.get(
                "https://ifconfig.me/ip", proxies=proxies, timeout=10
            )

            if response.status_code == 200:
                self.req.proxies.update(proxies)
                print("Proxy set up successfully")
            else:
                print(f"Proxy test failed with status code: {response.status_code}")

        except requests.RequestException as e:
            print(f"Error testing proxy: {e}")
