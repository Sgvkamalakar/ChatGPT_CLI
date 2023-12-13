import os,re,json,logging,argparse
from config import Config
from session import ChatSession
from PromptsManager import PromptsManager
from colors import *

__version__ = '0.1.0'
lg = logging.getLogger(__name__)
home = os.path.expanduser('~')


def main():
    parser = argparse.ArgumentParser(description="A simple CLI for ChatGPT API", epilog="", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('prompt', metavar="PROMPT", type=str, nargs='?', help="your prompt, leave it empty to run REPL. you can use @ to load prompt from ~/.ai_py_prompts.json")
    parser.add_argument('-s', '--system', type=str, help="system message to use at the beginning of the conversation. if starts with @, the message will be located through ~/.ai_py_prompts.json")
    parser.add_argument('-c', '--conversation', action='store_true', help="enable conversation, which means all the messages will be sent to the API, not just the last one. This is only useful to REPL")
    parser.add_argument('-v', '--verbose', action='store_true', help="verbose mode, show execution info and role in the message")
    parser.add_argument('-d', '--debug', action='store_true', help="debug mode, enable logging")

    args = parser.parse_args()

    config_file = os.path.join(home, '.ai_py_config.json')
    if os.path.exists(config_file):
        with open(config_file) as f:
            config = json.load(f)
        for k, v in config.items():
            setattr(Config, k, v)

    env_api_key = os.environ.get('AI_PY_API_KEY')
    if env_api_key:
        Config.api_key = env_api_key
    env_api_base_url = os.environ.get('AI_PY_API_BASE_URL')
    if env_api_base_url:
        Config.api_base_url = env_api_base_url
        
    # override config from args
    Config.verbose = args.verbose
    Config.debug = args.debug
    if Config.debug:
        logging.basicConfig(level=logging.DEBUG)
        
    # check config
    if not Config.api_key:
        print(red('ERROR: missing API key'))
        print(f'Please set the environment variable AI_PY_API_KEY or set api_key in {config_file}')
        exit(1)
    if not Config.api_base_url:
        print(red('ERROR: missing API base url'))
        print(f'Please set the environment variable AI_PY_API_BASE_URL or set api_base_url in {config_file}')
        exit(1)

    # Initialize prompts
    pm = PromptsManager()
    pm.load_from_file()

    # Create session
    session = ChatSession(Config.api_base_url, Config.api_key, conversation=args.conversation, messages=pm.new_messages(args.system))
    if args.prompt:
        chat(session, pm, args.prompt)
    else:
        reply(session, pm)


def chat(session, pm, prompt):
    user_message = pm.new_user_message(prompt)
    try:
        res_message = session.chat(user_message)
    except TimeoutError:
        print(red('ERROR: timeout'))
        return
    except KeyboardInterrupt:
        print('chat interrupted')
        return
    if Config.verbose:
        print_message(user_message)
    print_message(res_message)


def reply(session, pm):
    user_name = ""
    magenta=esc(35)
    while not user_name: 
        user_name = input(f"{magenta}Bot>Hello user 👋!! Enter your name to start the converstation: ")
    green_start = esc(32)

        
    while True:
        try:
            prompt = input(f'{green_start}{user_name}>')
        except (KeyboardInterrupt, EOFError):
            print(END, end='')
            print('exit')
            print(red(f'Exiting'))
            break
        print(END, end='')
        if not prompt:
            continue
        print()
        if prompt in ['exit', 'stop','quit','revoke']:
            print(red(f'Exiting'))
            break
        
        if prompt.startswith('!'):
            try:
                run_command(session, pm, prompt)
            except Exception as e:
                print(red(f'Exiting'))
            break

        chat(session, pm, prompt)


command_set_keys = ['model', 'params', 'system', 'conversation', 'verbose']

def run_command(session, pm, prompt):
    sp = prompt.split(' ')
    command = sp[0][1:]
    args = sp[1:]
    if command == 'set':
        set_key = args[0]
        assert set_key in command_set_keys, f'set key is not one of {command_set_keys}'

        if set_key == 'verbose':
            Config.verbose = bool(args[1])
        elif set_key == 'conversation':
            session.conversation = bool(args[1])
        elif set_key == 'system':
            session.update_system_message(pm.new_system_message(' '.join(args[1:])))
        elif set_key == 'params':
            session.params[args[1]] = args[2]
        elif set_key == 'model':
            session.model = args[1]
    else:
        raise Exception(f'unknown command: {command}')


inline_code_re = re.compile(r'`([^\n`]+)`')
multiline_code_re = re.compile(r'```\w*\n([^`]+)\n```')


def print_message(message):
    role = message['role']
    role_with_padding = f' {role} '
    content = message['content'].strip()

    if role != 'user':
        content = multiline_code_re.sub(lambda m: m.group(0).replace(m.group(1), cyan(m.group(1))), content)
        content = inline_code_re.sub(lambda m: m.group(0).replace(m.group(1), cyan(m.group(1))), content)

    content_color = lambda s: s
    role_color = white_hl
    
    if role == 'user':
        content_color = green
        role_color = green_hl

    s = content_color(content)
    if (Config.verbose):
        s = f'{role_color(role_with_padding)} {s}'

    print('Bot>',s + '\n')


if __name__ == '__main__':
    main()
