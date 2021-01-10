# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import hashlib
import mimetypes
import os
from datetime import datetime

from scrapy import Request
from scrapy.pipelines.files import FilesPipeline
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.python import to_bytes
from twisted.enterprise import adbapi

from KugouMusicSpiderRedis.items import SingerItem, MusicItem


class KugoumusicspiderPipeline:
    def process_item(self, item, spider):
        return item


class KugouMusicPipeline(FilesPipeline):
    """
    下载音频文件
    """

    def get_media_requests(self, item, info):
        if isinstance(item, MusicItem):
            url = item['play_url']
            yield Request(url)

    def file_path(self, request, response=None, info=None, *, item=None):
        # media_guid = hashlib.sha1(to_bytes(request.url)).hexdigest()
        author_name = item['author_name']
        media_guid = item['name']
        media_ext = os.path.splitext(request.url)[1]
        if media_ext not in mimetypes.types_map:
            media_ext = ''
            media_type = mimetypes.guess_type(request.url)[0]
            if media_type:
                media_ext = mimetypes.guess_extension(media_type)
        return f'{author_name}/{media_guid}{media_ext}'

    def item_completed(self, results, item, info):
        if isinstance(item, MusicItem):
            file_paths = [x['path'] for ok, x in results if ok]
            if file_paths:
                item['play_path'] = file_paths[0]
        return item


class KugouImagePipeline(ImagesPipeline):
    """
    处理文件下载路径，并将路径信息存入item
    """

    def get_media_requests(self, item, info):
        if isinstance(item, SingerItem):
            url = item['pic_url']
            yield Request(url)

    def file_path(self, request, response=None, info=None, *, item=None):
        if isinstance(item, SingerItem):
            name = item['name']
            image_guid = hashlib.sha1(to_bytes(request.url)).hexdigest()
            return f'{name}/{image_guid}.jpg'

    def item_completed(self, results, item, info):
        if isinstance(item, SingerItem):
            file_paths = [x['path'] for ok, x in results if ok]
            if file_paths:
                item['pic_path'] = file_paths[0]
        return item


class MysqlTwistedPipeline(object):
    """
    异步方式插入数据库
    """

    def __init__(self, db_pool):
        self.db_pool = db_pool

    @classmethod
    def from_settings(cls, settings):
        from MySQLdb.cursors import DictCursor
        db_params = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWORD'],
            charset='utf8',
            cursorclass=DictCursor,
            use_unicode=True
        )
        db_pool = adbapi.ConnectionPool('MySQLdb', **db_params)
        return cls(db_pool)

    def process_item(self, item, spider):
        query = self.db_pool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)

    def handle_error(self, failure, item, spider):
        print(failure)

    def do_insert(self, cursor, item):
        params = list()
        cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(item, SingerItem):
            insert_sql = """
                insert into singer
                (name,author_id,index_url,pic_url,pic_path,brief,first_create_time,update_time)
                values 
                (%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE 
                author_id=VALUES(author_id),
                index_url=VALUES(index_url),
                pic_url=VALUES(pic_url),
                brief=VALUES(brief),
                update_time=VALUES(update_time);
            """
            params.append(item.get('name', ''))
            params.append(item.get('author_id', ''))
            params.append(item.get('index_url', ''))
            params.append(item.get('pic_url', ''))
            params.append(item.get('pic_path', ''))
            params.append(item.get('brief', ''))
            params.append(cur_time)
            params.append(cur_time)

            cursor.execute(insert_sql, tuple(params))

        elif isinstance(item, MusicItem):
            pass
            insert_sql = """
                        insert into music
                        (hash,name,lyrics,play_url,play_path,audio_id,author_id,author_name,audio_name,album_name,album_id,img_url,have_mv,video_id,first_create_time,update_time)
                        values 
                        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON DUPLICATE KEY UPDATE 
                        hash=VALUES(hash),
                        play_url=VALUES(play_url),
                        img_url=VALUES(img_url),
                        update_time=VALUES(update_time);
                    """

            params.append(item.get('hash', ''))
            params.append(item.get('name', ''))
            params.append(item.get('lyrics', ''))
            params.append(item.get('play_url', ''))
            params.append(item.get('play_path', ''))
            params.append(item.get('audio_id', ''))
            params.append(item.get('author_id', ''))
            params.append(item.get('author_name', ''))
            params.append(item.get('audio_name', ''))
            params.append(item.get('album_name', ''))
            params.append(item.get('album_id', ''))
            params.append(item.get('img_url', ''))
            params.append(item.get('have_mv', ''))
            params.append(item.get('video_id', ''))
            params.append(cur_time)
            params.append(cur_time)

            cursor.execute(insert_sql, tuple(params))
