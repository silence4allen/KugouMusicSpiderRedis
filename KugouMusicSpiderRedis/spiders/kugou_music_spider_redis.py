import json
import re
from urllib import parse

from scrapy import Request
from scrapy_redis.spiders import RedisSpider

from KugouMusicSpiderRedis.items import MusicItem, SingerItem


class KugouMusicSpiderRedisSpider(RedisSpider):
    name = 'kugou_music_spider_redis'
    allowed_domains = ['https://www.kugou.com/']
    redis_key = "kugou_music"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:84.0) Gecko/20100101 Firefox/84.0",
    }
    cookies = {
        "kg_mid": "63c14870a78d3069de32069d62394a5e",
        "Hm_lvt_aedee6983d4cfc62f509129360d6bb3d": "1610034343",
        "kg_dfid": "10GLmq163pCh131m8D0BQ5rx",
        "kg_dfid_collect": "d41d8cd98f00b204e9800998ecf8427e"
    }

    def parse(self, response):
        """
        根据酷狗首页获取'更多'歌手连接（即歌手首页）
        :param response:
        :return:
        """
        singer_index_url = response.xpath('//div[@id="tabMenu"]//a[@class="more"]/@href').extract_first()
        singer_index_url = parse.urljoin(response.url, singer_index_url)
        yield Request(
            url=singer_index_url,
            callback=self.parse_singer_index,
            dont_filter=True
        )

    def parse_singer_index(self, response):
        """
        解析歌手首页，只爬取前18位歌手数据
        :param response:
        :return:
        """
        head_singers = response.xpath('//ul[@id="list_head"]/li')
        for singer_info in head_singers:
            singer_url = singer_info.xpath('./a/@href').extract_first()
            match_re = re.match(".*?(\d+).*", singer_url)
            if match_re:
                author_id = match_re.group(1)
                name = singer_info.xpath('./a/@title').extract_first()
                pic_url = singer_info.xpath('./a/img/@_src').extract_first()

                singer_item = SingerItem()
                singer_item.update({
                    "name": name,
                    "author_id": author_id,
                    "index_url": singer_url,
                    "pic_url": pic_url
                })
                yield Request(
                    url=singer_url,
                    callback=self.parse_singer_detail,
                    meta={"singer_item": singer_item},
                    dont_filter=True
                )

    def parse_singer_detail(self, response):
        """
        解析歌手详情页面，提取歌曲
        :param response:
        :return:
        """
        singer_item = response.meta.get('singer_item')

        brief = response.xpath('//div[@class="intro"]/p/text()').extract_first()
        singer_item.update({
            "brief": brief
        })
        yield singer_item

        musics = response.xpath('//ul[@id="song_container"]/li')
        for music in musics:
            music_hash = music.xpath('./a/input/@value').extract_first()
            match_re = re.match(".*\|(.*)\|.*", music_hash)
            if match_re:
                music_hash = match_re.group(1)
                if music_hash:
                    url = 'https://wwwapi.kugou.com/yy/index.php?r=play/getdata&hash={}'.format(music_hash)
                    yield Request(
                        url=url,
                        headers=self.headers,
                        cookies=self.cookies,
                        callback=self.parse_music_info,
                        dont_filter=True
                    )

    def parse_music_info(self, response):
        """
        获取歌曲album_id
        :param response:
        :return:
        """
        res = json.loads(response.text)
        status = res.get('status')
        err_code = res.get('err_code')
        if status == 1 and err_code == 0:
            get_detail = response.meta.get('get_detail')
            data = res.get('data', {})
            if data:
                if get_detail:
                    music_item = MusicItem()
                    music_item.update({
                        "hash": data.get('hash'),
                        "name": data.get('song_name'),
                        "lyrics": data.get('lyrics'),
                        "play_url": data.get('play_url'),
                        "audio_id": data.get('audio_id'),
                        "author_id": data.get('author_id'),
                        "author_name": data.get('author_name'),
                        "audio_name": data.get('audio_name'),
                        "album_name": data.get('album_name'),
                        "album_id": data.get('album_id'),
                        "img_url": data.get('img'),
                        "have_mv": data.get('have_mv'),
                        "video_id": data.get('video_id')
                    })
                    yield music_item
                else:
                    album_id = data.get('album_id')
                    if album_id is not None:
                        url = '{}&album_id={}'.format(response.url, album_id)
                        yield Request(
                            url=url,
                            headers=self.headers,
                            cookies=self.cookies,
                            callback=self.parse_music_info,
                            meta={'get_detail': True},
                            dont_filter=True
                        )
