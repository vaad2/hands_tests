import re
import asyncio
import logging

import httpx
import uvloop

logging.getLogger().setLevel(logging.DEBUG)

re_search = re.compile('(\d?(:?\d{3})?\d{7})', re.IGNORECASE | re.MULTILINE)
re_clean = re.compile('[ \-\(\+\)]', re.IGNORECASE | re.MULTILINE)

extractors_cache = {}


def extract_phones(content, extractor=None):
    re_cleaner = None
    phones = set()
    if extractor is None:
        re_cleaner = re_clean
        re_finder = re_search
    else:
        if 'cleaner' in extractor:
            if not extractor['cleaner'] in extractors_cache:
                extractors_cache[extractor['cleaner']] = \
                    re.compile(extractor['cleaner'],
                               re.IGNORECASE | re.MULTILINE)

            re_cleaner = extractors_cache[extractor['cleaner']]

        if extractor['finder'] not in extractors_cache:
            extractors_cache[extractor['finder']] = re.compile(
                extractor['finder'], re.IGNORECASE | re.MULTILINE)

        re_finder = extractors_cache[extractor['finder']]

    if re_cleaner:
        content = re_cleaner.sub('', content)

    for item in re_finder.finditer(content):
        try:
            phone = str(item.groups(0)[0])
            phone = re_clean.sub('', phone)
            # print('PHONE', phone, 'grs', item.groups())
            if len(phone) == 7:
                phone = '8495' + phone

            phone = '8' + phone[1:]

            phones.add(phone)
        except Exception as e:
            logging.error('finder error {}'.format(e))

    return phones


async def worker(queue, extracting_result):
    while True:
        try:
            data = await queue.get()

            async with httpx.AsyncClient() as client:
                logging.debug('try to get {}'.format(data['url']))
                response = await client.get(data['url'])
                if response.status_code == 200:

                    phones = extract_phones(
                        response.text, data.get('extractor', None))
                    if len(phones):
                        src_phones = set(data['phones'])
                        logging.debug('result for {}'.format(data['url']))
                        result = {
                            'found': phones & src_phones,
                            'not_found': phones - src_phones,
                            'new_phones': src_phones - phones}

                        logging.debug(result)
                        extracting_result.append(result)
                else:
                    logging.error('some details about error')

            queue.task_done()
        except Exception as e:
            logging.error(str(e))


# lCenterPhone":"+74951370720"}
async def test(queue):
    items = [{
        'url': 'https://hands.ru/company/about/',
        'phones': ['84951370720'],
        'extractor': {
            'finder': '(\+\d{11})'
        }}, {
        'url': 'https://repetitors.info/',
        'phones': ['84955405676'],
        'extractor': {
            'finder': '(\d \(\d{3}\) \d{3}-\d{2}-\d{2})'
        }}, {
        'url': 'https://on-foot.ru/about/',
        'phones': ['83832040173']
    }]

    for item in items:
        await queue.put(item)


async def main():
    tasks = []
    max_workers = 2
    queue = asyncio.Queue()
    extracting_result = []

    await test(queue)

    for i in range(max_workers):
        task = asyncio.create_task(worker(queue, extracting_result))
        tasks.append(task)

    await queue.join()

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)


uvloop.install()
asyncio.run(main())
