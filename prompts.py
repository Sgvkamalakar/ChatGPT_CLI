import os,json,logging,re

home = os.path.expanduser('~')
lg = logging.getLogger(__name__)
shortcut_re = re.compile(r'@(\w+)')

class PromptsManager:
    def __init__(self):
        self.data = {}

    def load_from_file(self):
        prompts_file = os.path.join(home, '.ai_py_prompts.json')
        if os.path.exists(prompts_file):
            with open(prompts_file) as f:
                self.data = json.load(f)
        lg.debug(f'prompts loaded: {self.data}')

    def get(self, role, name, default=None):
        return self.data.get(role, {})[name]

    def format_prompt(self, prompt, role):
        def handle_match(m):
            try:
                return self.get(role, m.group(1))
            except KeyError:
                return m.group(0)
        return shortcut_re.sub(handle_match, prompt)

    def new_messages(self, system_prompt):
        if system_prompt:
            return [{
                'role': 'system',
                'content': self.format_prompt(system_prompt, 'system'),
            }]
        return []

    def new_user_message(self, prompt):
        return {
            'role': 'user',
            'content': self.format_prompt(prompt, 'user'),
        }
