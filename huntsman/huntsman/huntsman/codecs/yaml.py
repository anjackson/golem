# -*- coding: utf-8 -*-
""" A JSON codec for Frontera. Implemented using native json library.
"""
from __future__ import absolute_import
import yaml
import six
from base64 import b64decode, b64encode
from frontera.core.codec import BaseDecoder, BaseEncoder
from w3lib.util import to_unicode, to_bytes


def _prepare_request_message(request):
    return {'url': request.url,
            'method': request.method,
            'headers': request.headers,
            'cookies': request.cookies,
            'meta': request.meta}


def _prepare_links_message(links):
    return [_prepare_request_message(link) for link in links]


def _prepare_response_message(response, send_body):
    return {'url': response.url,
            'status_code': response.status_code,
            'meta': response.meta,
            'body': b64encode(response.body) if send_body else None}


class Encoder(BaseEncoder):
    def __init__(self, request_model, *a, **kw):
        self._request_model = request_model
        self.send_body = kw.pop('send_body', False)

    def encode(self, obj):
        return yaml.dump(obj).encode('utf-8')

    def encode_page_crawled(self, response):
        return self.encode({
            'type': 'page_crawled',
            'r': _prepare_response_message(response, self.send_body)
        })

    def encode_links_extracted(self, request, links):
        return self.encode({
            'type': 'links_extracted',
            'r': _prepare_request_message(request),
            'links': _prepare_links_message(links)
        })

    def encode_request_error(self, request, error):
        return self.encode({
            'type': 'request_error',
            'r': _prepare_request_message(request),
            'error': error
        })

    def encode_request(self, request):
        return self.encode(_prepare_request_message(request))

    def encode_update_score(self, request, score, schedule):
        return self.encode({'type': 'update_score',
                            'r': _prepare_request_message(request),
                            'score': score,
                            'schedule': schedule})

    def encode_new_job_id(self, job_id):
        return self.encode({
            'type': 'new_job_id',
            'job_id': int(job_id)
        })

    def encode_offset(self, partition_id, offset):
        return self.encode({
            'type': 'offset',
            'partition_id': int(partition_id),
            'offset': int(offset)
        })

    def encode_stats(self, stats):
        return self.encode({
            'type': 'stats',
            'stats': stats
        })


class Decoder(BaseDecoder):
    def __init__(self, request_model, response_model, *a, **kw):
        self._request_model = request_model
        self._response_model = response_model

    def _response_from_object(self, obj):
        url = obj['url']
        request = self._request_model(url=url,
                                      meta=obj['meta'])
        return self._response_model(url=url,
                                    status_code=obj['status_code'],
                                    body=b64decode(obj['body']) if obj['body'] is not None else None,
                                    request=request)

    def _request_from_object(self, obj):
        return self._request_model(url=obj['url'],
                                   method=obj['method'],
                                   headers=obj['headers'],
                                   cookies=obj['cookies'],
                                   meta=obj['meta'])

    def decode(self, message):
        message = yaml.load(message.decode('utf-8'))
        if message['type'] == 'links_extracted':
            request = self._request_from_object(message['r'])
            links = [self._request_from_object(link) for link in message['links']]
            return ('links_extracted', request, links)
        if message['type'] == 'page_crawled':
            response = self._response_from_object(message['r'])
            return ('page_crawled', response)
        if message['type'] == 'request_error':
            request = self._request_from_object(message['r'])
            return ('request_error', request, message['error'])
        if message['type'] == 'update_score':
            return ('update_score', self._request_from_object(message['r']), message['score'], message['schedule'])
        if message['type'] == 'new_job_id':
            return ('new_job_id', int(message['job_id']))
        if message['type'] == 'offset':
            return ('offset', int(message['partition_id']), int(message['offset']))
        if message['type'] == 'stats':
            return ('stats', message['stats'])
        raise TypeError('Unknown message type')

    def decode_request(self, message):
        obj = yaml.load(message.decode('utf-8'))
        return self._request_model(url=obj['url'],
                                   method=obj['method'],
                                   headers=obj['headers'],
                                   cookies=obj['cookies'],
                                   meta=obj['meta'])