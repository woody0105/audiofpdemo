from datetime import datetime
from typing import Dict, List, Tuple
from elasticsearch_dsl import Document, Date, Integer, Keyword, Text, connections, Binary, Boolean
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import random

ELASTIC_USER = 'elastic'
ELASTIC_PASS = 'qNq0dMcBw3Zs1hAFGnTi'

class Fingerprints(Document):
    hash = Keyword()
    song_id = Integer()
    song_name = Text()
    song_title = Text()
    artist = Text()
    offset =Integer()

    class Index:
        name = 'fingerprints'

class Songs(Document):
    song_name = Text()
    song_title = Text()
    artist = Text()
    fingerprinted = Boolean()
    file_sha1 = Text()
    total_hashes = Integer()
    date_created = Date()
    class Index:
        name = 'songs'

class Es:
    def __init__(self):
        connections.create_connection(hosts=['localhost'], http_auth=(ELASTIC_USER, ELASTIC_PASS))
        self.elasticClient = Elasticsearch(
            ["localhost:9200"], http_auth=(ELASTIC_USER, ELASTIC_PASS)
        )
    def insert_hash(self, title, artist, song_id:int, fingerprint: str, offset:int):
        """
        Inserts a single fingerprint into the database.

        :param title: title of the song
        :param artist: song artist
        :param fingerprint: Part of a sha1 hash, in hexadecimal format
        :param song_id: Song identifier this fingerprint is off
        :param offset: The offset this fingerprint is from.
        """
        fingerprint = Fingerprints(song_id=song_id, song_title=title, artist=artist, hash=fingerprint, offset=offset)
        fingerprint.save()

    def insert_hashes(self, title, artist, song_id: int, hashes: List[Tuple[str, int]], batch_size: int = 1000):
        """
        Insert a multitude of fingerprints.
        :param song_id: Song identifier the fingerprints belong to
        :param hashes: A sequence of tuples in the format (hash, offset)
            - hash: Part of a sha1 hash, in hexadecimal format
            - offset: Offset this hash was created from/at.
        :param batch_size: insert batches.
        """

        data = []
        for hsh, offset in hashes:
            document = {}
            document['song_id'] = song_id
            document['hash'] = hsh
            document['song_title'] = title
            document['artist'] = artist
            document['offset'] = offset

            data.append({
                '_op_type': 'create',
                '_index': 'fingerprints',
                'doc': document
                # 'doc_as_upsert': True
            })

        bulk(self.elasticClient, data, index='fingerprints')

    def insert_song(self, song_name: str, title: str, artist: str, file_hash: str, total_hashes: int) -> int:
        """
        Inserts a song name into the database, returns the new
        identifier of the song.

        :param song_name: The name of the song.
        :param file_hash: Hash from the fingerprinted file.
        :param total_hashes: amount of hashes to be inserted on fingerprint table.
        :return: the inserted id.
        """
        id = random.randint(1, 1000000000000)
        song = Songs(meta={'id': id}, song_name=song_name, song_title=title, artist=artist, file_sha1=file_hash, total_hashes=total_hashes)
        song.save()
        return id

    def set_song_fingerprinted(self, song_id):
        """
        Sets a specific song as having all fingerprints in the database.

        :param song_id: song identifier.
        """
        song = Songs.get(id=song_id)
        song.fingerprinted = True
        song.save()

    def get_songs(self):
        res = self.elasticClient.search(index="songs", body={"query": {"match": {"fingerprinted": True}}}, size=10000)
        return res['hits']['hits']

    def get_song_by_id(self, song_id: int):
        res = self.elasticClient.search(index="songs", body={"query": {"match":{"_id": song_id}}})
        return res['hits']['hits'][0]['_source']

    def return_matches(self, hashes, batch_size: int=1000):
        """
        Searches the database for pairs of (hash, offset) values.

        :param hashes: A sequence of tuples in the format (hash, offset)
            - hash: Part of a sha1 hash, in hexadecimal format
            - offset: Offset this hash was created from/at.
        :param batch_size: number of query's batches.
        :return: a list of (sid, offset_difference) tuples and a
        dictionary with the amount of hashes matched (not considering
        duplicated hashes) in each song.
            - song id: Song identifier
            - offset_difference: (database_offset - sampled_offset)
        """
        # Create a dictionary of hash => offset pairs for later lookups
        mapper = {}
        for hsh, offset in hashes:
            if hsh in mapper.keys():
                mapper[hsh].append(offset)
            else:
                mapper[hsh] = [offset]

        values = list(mapper.keys())

        # in order to count each hash only once per db offset we use the dic below
        dedup_hashes = {}

        results = []

        for index in range(0, len(values), batch_size):
            # Create our IN part of the query
            # query = self.SELECT_MULTIPLE % ', '.join([self.IN_MATCH] * len(values[index: index + batch_size]))

            res = self.elasticClient.search(index="fingerprints",
                            body={"query": {"terms": {"doc.hash": values[index: index+batch_size]}}}, size=1000000)

            query_res = res['hits']['hits']
            for doc in query_res:
                hsh = doc['_source']['doc']['hash']
                sid = doc['_source']['doc']['song_id']
                offset = doc['_source']['doc']['offset']
                if sid not in dedup_hashes.keys():
                    dedup_hashes[sid] = 1
                else:
                    dedup_hashes[sid] += 1
                #  we now evaluate all offset for each  hash matched
                for song_sampled_offset in mapper[hsh]:
                    results.append((sid, offset - song_sampled_offset))

        return results, dedup_hashes
