import urllib3


class HttpPool:
    pool: urllib3.PoolManager = urllib3.PoolManager()
