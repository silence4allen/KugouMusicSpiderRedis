# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SingerItem(scrapy.Item):
    name = scrapy.Field()
    author_id = scrapy.Field()
    index_url = scrapy.Field()
    pic_url = scrapy.Field()
    pic_path = scrapy.Field()
    brief = scrapy.Field()


class MusicItem(scrapy.Item):
    hash = scrapy.Field()
    name = scrapy.Field()
    lyrics = scrapy.Field()
    play_url = scrapy.Field()
    play_path = scrapy.Field()
    audio_id = scrapy.Field()
    author_id = scrapy.Field()
    author_name = scrapy.Field()
    audio_name = scrapy.Field()
    album_name = scrapy.Field()
    album_id = scrapy.Field()
    img_url = scrapy.Field()
    have_mv = scrapy.Field()
    video_id = scrapy.Field()
