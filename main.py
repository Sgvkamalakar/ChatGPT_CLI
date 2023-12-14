import os, re, json, logging, argparse
from config import Config
from session import ChatSession
from prompts import PromptsManager
from colors import *

__version__='0.1.0'
lg=logging.getLogger(__name__)
home=os.path.expanduser('~')
inline_code_re=re.compile(r'`([^\n`]+)`')
multiline_code_re=re.compile(r'```\w*\n([^`]+)\n```')

def main():
    parser=argparse.ArgumentParser(description="A simple CLI for ChatGPT", epilog="", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('prompt', metavar="PROMPT", type=str, nargs='?', help="Your prompt to start the conversation.")
    args=parser.parse_args()

    config_file=os.path.join(home, '.ai_py_config.json')
    if os.path.exists(config_file):
        with open(config_file) as f:
            config=json.load(f)
        for k, v in config.items():
            setattr(Config, k, v)

    env_api_key=os.environ.get('AI_PY_API_KEY')
    if env_api_key:
        Config.api_key=env_api_key
    env_api_base_url=os.environ.get('AI_PY_API_BASE_URL')
    if env_api_base_url:
        Config.api_base_url=env_api_base_url
        
    Config.verbose=True
    Config.debug=False  
        
    if not Config.api_key:
        print(red('ERROR: missing API key'))
        print(f'Please set the environment variable AI_PY_API_KEY or set api_key in {config_file}')
        exit(1)
    if not Config.api_base_url:
        print(red('ERROR: missing API base url'))
        print(f'Please set the environment variable AI_PY_API_BASE_URL or set api_base_url in {config_file}')
        exit(1)

    pm=PromptsManager()
    pm.load_from_file()

    session=ChatSession(Config.api_base_url, Config.api_key, conversation=False, messages=pm.new_messages(args.prompt))
    if args.prompt:
        chat(session, pm, args.prompt)
    else:
        reply(session, pm)

def chat(session, pm, prompt):
    user_message=pm.new_user_message(prompt)
    try:
        res_message=session.chat(user_message)
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
    user_name=""
    color=magenta_hl
    while not user_name: 
        user_name=input(f"{color('Bot>')} {magenta('Hello user 👋!! Enter your name to start the conversation: ')}")
        print('\n')
    green_start=esc(32)

    while True:
        try:
            role_color=green_hl
            role_with_padding=user_name+'>'
            
            prompt=input(f'{role_color(role_with_padding)}{green_start} ')

        except (KeyboardInterrupt, EOFError):
            print(END, end='')
            print('exit')
            print(red(f'Exiting'))
            break

        print(END, end='')
        if not prompt:
            continue
        print()
        if prompt in ['exit', 'stop','quit','bye']:
            print(red(f'Exiting'))
            break
        
        if prompt.startswith('!'):
            try:
                run_command(session, pm, prompt)
            except Exception as e:
                print(red(f'Exiting'))
            break

        chat(session, pm, prompt)


command_set_keys=['model', 'params', 'system', 'conversation', 'verbose']
def run_command(session, pm, prompt):
    sp=prompt.split(' ')
    command=sp[0][1:]
    args=sp[1:]
    if command=='set':
        set_key=args[0]
        assert set_key in command_set_keys, f'set key is not one of {command_set_keys}'

        if set_key=='verbose':
            Config.verbose=bool(args[1])
        elif set_key=='conversation':
            session.conversation=bool(args[1])
        elif set_key=='system':
            session.update_system_message(pm.new_system_message(' '.join(args[1:])))
        elif set_key=='params':
            session.params[args[1]]=args[2]
        elif set_key=='model':
            session.model=args[1]
    else:
        raise Exception(f'unknown command: {command}')

def print_message(message):
    role=message['role']
    role_with_padding=f'{role}>'
    content=message['content'].strip()
    
    if not content.startswith('stat:'):
        if role != 'user': 
            content=multiline_code_re.sub(lambda m: m.group(0).replace(m.group(1), magenta(m.group(1))), content)
            content=inline_code_re.sub(lambda m: m.group(0).replace(m.group(1), white(m.group(1))), content)
            
            content_color=white
            role_color=white_hl

            s=content_color(content)
            if Config.verbose:
                s=f'{role_color(role_with_padding)} {s}'
            s=s.replace('assistant', 'Bot')
            print(s+'\n')

if __name__=='__main__':
    main()
