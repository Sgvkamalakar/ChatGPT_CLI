class Config:
    api_key = 'YOUR_API_KEY'
    api_base_url = 'https://api.openai.com/v1/'
    gpt_model='gpt-3.5-turbo'
    default_params = {
        # 'max_tokens': 100,
        # 'temperature': 0.5,
        # 'top_p': 1,
        # 'frequency_penalty': 0.4,
    }
    timeout = None
    verbose = False
    debug = False
    
