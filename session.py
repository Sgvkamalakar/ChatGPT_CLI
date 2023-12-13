import os,json,logging
from colors import *
from urllib import request, parse
from urllib.error import HTTPError
from http.client import HTTPResponse, IncompleteRead
from config import Config

lg = logging.getLogger(__name__)
home = os.path.expanduser('~')
class ChatSession:
    def __init__(self, api_base_url, api_key, conversation=False, messages=None, model=None, params=None):
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.conversation = conversation
        if messages is None:
            messages = []
        self.messages = messages

        if not model:
            model = Config.gpt_model
        self.model = model

        if not params:
            params = Config.default_params
        self.params = params

    def chat(self, user_message, params_override=None):
        self.messages.append(user_message)
        res_message, data, messages = self.create_completion(params_override=params_override)
        if Config.verbose:
            print(blue(f'stat: sent_messages={len(messages)} total_messages={len(self.messages)} total_tokens={data["usage"]["total_tokens"]} tokens_price=~${"{:.6f}".format(data["usage"]["total_tokens"]/1000*0.002)}'))
        self.messages.append(res_message)
        return res_message

    def create_completion(self, params_override=None) -> tuple[dict, dict, list]:
        url = f'{self.api_base_url}chat/completions'
        headers = {
            'User-Agent': 'reorx/ai',
            'Authorization': f'Bearer {self.api_key}',
        }

        if self.conversation:
            messages = self.messages
        else:
            messages = list(filter(lambda x: x['role'] == 'system', self.messages))
            # assume the last message is always the user message
            messages.append(self.messages[-1])

        data = dict(self.params)
        if params_override:
            data.update(params_override)
        data.update(
            model=Config.gpt_model,
            messages=messages,
        )

        try:
            res, body_b = http_request('POST', url, headers=headers, data=data, logger=lg, timeout=Config.timeout)
        except HTTPError as e:
            raise RequestError(e.status, e.read().decode()) from None
        res_data = json.loads(body_b)
        res_message = res_data['choices'][0]['message']

        return res_message, res_data, messages

def http_request(method, url, params=None, headers=None, data: Optional[Union[dict, list, bytes]] = None, timeout=None, logger=None) -> Tuple[HTTPResponse, bytes]:
    if params:
        url = f'{url}?{parse.urlencode(params)}'
    if not headers:
        headers = {}
    if data and isinstance(data, (dict, list)):
        data = json.dumps(data, ensure_ascii=False).encode()
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
    if logger:
        logger.debug(f'request: {method} {url}\nheaders: {headers}\ndata: {data}')
    req = request.Request(url, method=method, headers=headers, data=data)
    res = request.urlopen(req, timeout=timeout)
    try:
        body_b: bytes = res.read()
    except IncompleteRead as e:
        body_b: bytes = e.partial
    if logger:
        logger.debug(f'response: {res.status}, {body_b}')
    return res, body_b


class RequestError(Exception):
    def __init__(self, status, body) -> None:
        self.status = status
        self.body = body

    def __str__(self):
        return f'{self.__class__.__name__}: {self.status}, {self.body}'



