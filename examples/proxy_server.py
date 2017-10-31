"""Run a local proxy server that distributes
   incoming requests to external proxies."""

import asyncio
import logging
import aiohttp

from proxybroker import Broker


async def get_pages(urls, proxy_url):
    tasks = [
        fetch_page(url, aiohttp.ProxyConnector(proxy_url)) for url in urls]
    for task in asyncio.as_completed(tasks):
        url, content = await task
        print('url: %s; content: %.100s' % (url, content))


async def fetch_page(url, conn):
    resp = None
    try:
        with aiohttp.ClientSession(connector=conn) as session:
            async with session.get(url) as response:
                logger.info('url: %s; status: %d' % (url, response.status))
                resp = await response.read()
    except (aiohttp.errors.ClientOSError, aiohttp.errors.ClientResponseError,
            aiohttp.errors.ServerDisconnectedError) as e:
        logger.error('url: %s; error: %r' % (url, e))
    finally:
        return (url, resp)


def main():
    host, port = '127.0.0.1', 8888  # by default

    loop = asyncio.get_event_loop()

    types = [('HTTP', 'High'), 'HTTPS', 'CONNECT:80']
    codes = [200, 301, 302]

    broker = Broker(max_tries=1, loop=loop)

    # Broker.serve() also supports all arguments that are accepted
    # Broker.find() method: data, countries, post, strict, dnsbl.
    broker.serve(host=host, port=port, types=types, limit=10, max_tries=3,
                 prefer_connect=True, min_req_proxy=5, max_error_rate=0.5,
                 max_resp_time=8, http_allowed_codes=codes, backlog=100)

    urls = ['http://httpbin.org/get', 'https://httpbin.org/get',
            'http://httpbin.org/redirect/1', 'http://httpbin.org/status/404']

    proxy_url = 'http://%s:%d' % (host, port)
    loop.run_until_complete(get_pages(urls, proxy_url))

    broker.stop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('Parser')

    main()
