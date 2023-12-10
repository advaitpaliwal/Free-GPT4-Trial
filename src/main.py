import aiohttp
import asyncio
import string
import random
import logging
import json
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

SUCCESS_STATUS = 'success'
FAILURE_STATUS = 'failure'


class Fetcher:
    def __init__(self, num_codes=10, concurrent_requests=5):
        self.num_codes = num_codes
        self.concurrent_requests = concurrent_requests
        self.ua = UserAgent()
        self.success_count = 0
        self.failure_count = 0

    def generate_random_code(self):
        characters = string.ascii_uppercase + string.digits
        code = ''.join(random.choice(characters) for _ in range(9))
        logging.info(f'Generated code: {code}')
        return code

    async def fetch(self, session, url, headers, semaphore):
        logging.info(f'Attempting to fetch URL: {url}')
        try:
            async with semaphore, session.get(url, headers=headers, timeout=5) as response:
                text = await response.text()
                logging.info(f'Completed fetching URL: {url}')
                logging.info(f'Response: {text}')
                if response.status != 200:
                    logging.error(
                        f'Error fetching URL: {url}, status: {response.status}')
                    return FAILURE_STATUS
                return self.parse_response(text)
        except Exception as e:
            logging.exception(f'Error fetching URL: {url}')
            return FAILURE_STATUS

    @staticmethod
    def parse_response(text):
        try:
            response_data = json.loads(text)
            if 'status' in response_data and response_data['status'] == SUCCESS_STATUS:
                return SUCCESS_STATUS
            else:
                return FAILURE_STATUS
        except json.JSONDecodeError:
            return FAILURE_STATUS

    async def run(self):
        random_codes = [self.generate_random_code()
                        for _ in range(self.num_codes)]
        semaphore = asyncio.Semaphore(self.concurrent_requests)
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch(session, f'https://chat.openai.com/public-api/referral/invites/{code}', self.get_headers(code), semaphore)
                     for code in random_codes]
            results = await asyncio.gather(*tasks)
            self.count_results(results)

        logging.info(
            f'Finished. Success: {self.success_count}, Failure: {self.failure_count}')

    def get_headers(self, code):
        return {
            'authority': 'chat.openai.com',
            'accept': '*/*',
            'user-agent': self.ua.random,
            'referer': f'https://chat.openai.com/invite/{code}',
        }

    def count_results(self, results):
        for result in results:
            if result == SUCCESS_STATUS:
                self.success_count += 1
            else:
                self.failure_count += 1


if __name__ == "__main__":
    logging.info('Starting main coroutine')
    fetcher = Fetcher()
    asyncio.run(fetcher.run())
    logging.info('Main coroutine finished')
