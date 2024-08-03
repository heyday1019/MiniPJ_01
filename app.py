import uuid
import os
import streamlit as st
import vertexai
from openai import OpenAI
from gpt import get_llm, load_gemini_model # gpt.py로부터 get_llm() 함수를 임포트.
from dalle import get_image_by_dalle # dalle.py로부터 get_image_by_dalle() 함수를 임포트.

# Credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "Jemini-project.json"

# Initialize Vertex AI
vertexai.init(project="my-mini-project-37928")

# Set page configuration
st.set_page_config(
    page_title="📚Kids authors",
    layout='wide',
    menu_items={
        'About': "Kids authors is an interactive storybook experience using Gemini AI and Dalle"
    },
    initial_sidebar_state='expanded'
)

st.title(f"📚Kids authors")

# API Keys (initialize in session state if not in secrets)
if 'openai_api_key' not in st.session_state:
    st.session_state['openai_api_key'] = st.secrets.get("OPENAI_API_KEY", "")


# Session state variables for story data
if 'data_dict' not in st.session_state:
    st.session_state['data_dict'] = {}
if 'oid_list' not in st.session_state:
    st.session_state['oid_list'] = []

# OpenAI API key handling
if 'openai_api_key' not in st.session_state:
    st.session_state['openai_api_key'] = ''
if 'apiBox_state' not in st.session_state:
    st.session_state['apiBox_state'] = False

# Genre input handling
if 'genre_input' not in st.session_state:
    st.session_state['genre_input'] = '아기 펭귄 보물이의 모험'
if 'genreBox_state' not in st.session_state:
    st.session_state['genreBox_state'] = True

# OpenAI API Key authentication function
def auth():
    os.environ['OPENAI_API_KEY'] = st.session_state.openai_api_key
    st.session_state.genreBox_state = False
    st.session_state.apiBox_state = True

# Sidebar UI
with st.sidebar:
    st.header('📚Kids authors')
    st.markdown('''
    Kids authors는 아이들을 위한 동화를 생성하는 인공지능입니다. Gemini AI와 Dalle를 사용하여 스토리가 진행됩니다.
    ''')
    st.info('''
            **Note:**
            - Dalle 구동을 위하여 OpenAI API Key를 입력하세요. 
            - Story는 Gemini AI가 생성합니다.
            ''')

    # OpenAI Key input form
    with st.form(key='API Keys'):
        openai_key = st.text_input(
            label='OpenAI API Key',
            key='openai_api_key',
            type='password',
            disabled=st.session_state.apiBox_state,
            help='OpenAI API key는 https://platform.openai.com/account/api-keys 에서 발급 가능합니다.'
        )
        btn = st.form_submit_button(label='Submit', on_click=auth)

    # Usage guide and example links
    with st.expander('사용 가이드'):
        st.markdown('''
        - 위의 입력 칸에 <OpenAI API Key>를 작성 후 [Submit] 버튼을 누르세요. 
        - 그 후 우측 화면에 주제나 주인공에 대한 서술을 묘사하고 [시작!] 버튼을 누르세요.
        - 스토리가 시작되면 선택지가 나오고 원하는 내용을 선택하면 내용이 전개합니다.
        ''')

    with st.expander('더 많은 예시 보러가기'):
        st.write('기존 발행된 PDF 링크 확인')

# Warning if OpenAI API Key is not provided
if not openai_key.startswith('sk-'):
    st.warning('OpenAI API Key가 입력되지 않았습니다.', icon='⚠')

# 화면에 출력할 스토리, 질문, 선택지, 이미지를 반환하는 함수.
def get_story_and_image(user_choice, history):
    llm_model = get_llm(history, user_choice)
    llm_generation_result = llm_model

    response_list = llm_generation_result.split("\n")

    choices = []
    img_prompt = None  
    
    if len(response_list) > 1 and response_list[-1].startswith('Dalle Prompt Start!'):
        img_prompt = response_list[-1]
        dalle_img = get_image_by_dalle(img_prompt)
    else:
        dalle_img = None

    responses = list(filter(lambda x: x != '' and x != '-- -- --', response_list))
    responses = list(filter(lambda x: not x.startswith('Dalle Prompt') and not x.startswith('Image prompt'), responses))
    responses = [s for s in responses if s.strip()]

    story = ""
    decisionQuestion = None 

    for response in responses:
        response = response.strip()
        if response.startswith('선택지:'):
            decisionQuestion = '**' + response + '**'
        elif response[1] == '.':
            choices.append(response)
        else:
            story += response + '\n'

    if img_prompt:
        story = story.replace(img_prompt, '')

    return {
        'story': story, 
        'decisionQuestion': decisionQuestion,
        'choices': choices,
        'dalle_img': dalle_img
    }

@st.cache_data(show_spinner='Generating your story...')  # Remove experimental_allow_widgets
def get_output(_pos: st.empty, oid='', genre='', history=''):

    if oid:
        st.session_state['genreBox_state'] = True
        st.session_state[f'expanded_{oid}'] = False # 펼쳐졌던 것을 닫기 위한 값
        st.session_state[f'radio_{oid}_disabled'] = True # 라디오 버튼을 닫기 위한 값
        st.session_state[f'submit_{oid}_disabled'] = True # 진행하기 버튼을 닫기 위한 값

        user_choice = st.session_state[f'radio_{oid}']
    
    if genre:         
        st.session_state['genreBox_state'] = False
        user_choice = genre
    #   history = "" # Initialize history for the first story part
        if not history:
            history = ""

    with _pos:
        data = get_story_and_image(user_choice, history)  # Pass history to get_story_and_image
        history += f"Human: {user_choice}\nAI: {data['story']}\n"
        add_new_data(data['story'], data['decisionQuestion'], data['choices'], data['dalle_img'], history) 
        
def generate_content(story, decisionQuestion, choices: list, img, oid):
    if f'expanded_{oid}' not in st.session_state:
        st.session_state[f'expanded_{oid}'] = True # 새로운 스토리를 펼치기 위한 값
    if f'radio_{oid}_disabled' not in st.session_state:
        st.session_state[f'radio_{oid}_disabled'] = False # 4개의 선택지를 선택하는 라디오 버튼을 열기 위한 값
    if f'submit_{oid}_disabled' not in st.session_state:
        st.session_state[f'submit_{oid}_disabled'] = False # 진행하기 버튼을 열기 위한 값
    story_pt = list(st.session_state["data_dict"].keys()).index(oid) + 1
    expander = st.expander(f'Part {story_pt}', expanded=st.session_state[f'expanded_{oid}'])
    col1, col2 = expander.columns([0.65, 0.35])
    empty = st.empty()
    if img:
        col2.image(img, width=40, use_column_width='always')
    
    with col1:
        st.write(story)

        if decisionQuestion and choices:
            with st.form(key=f'user_choice_{oid}'): 
                st.radio(decisionQuestion, choices, disabled=st.session_state[f'radio_{oid}_disabled'], key=f'radio_{oid}')
                st.form_submit_button(
                    label="진행하기", 
                    disabled=st.session_state[f'submit_{oid}_disabled'], 
                    on_click=get_output, args=[empty], kwargs={'oid': oid}
                )


def add_new_data(*data):
    '''
    data 내부 구조
    'story': 화면에 출력할 스토리
    'decisionQuestion': 화면에 출력할 질문. '다음은 어떻게 해야할까요?'
    'choices': 화면에 출력할 실제 4개의 선택지.
    'dalle_img': 화면에 출력할 달리 이미지
    '''
    oid = str(uuid.uuid4())

    st.session_state['oid_list'].append(oid)
    st.session_state['data_dict'][oid] = data
    
# Genre Input widgets
with st.container():
    col_1, col_2, col_3 = st.columns([8, 1, 1], gap='small')
    
    col_1.text_input(
        label='Enter the theme/genre of your story',
        key='genre_input',
        placeholder='Enter the theme of which you want the story to be', 
        disabled=st.session_state.genreBox_state
    )
    col_2.write('')
    col_2.write('')
    col_2_cols = col_2.columns([0.5, 6, 0.5])
    col_2_cols[1].button(
        ':arrows_counterclockwise: &nbsp; Clear', 
        key='clear_btn',
        on_click=lambda: setattr(st.session_state, "genre_input", ''),
        disabled=st.session_state.genreBox_state
    )
    col_3.write('')
    col_3.write('')
    begin = col_3.button(
        '시작!',
        on_click=get_output, args=[st.empty()], kwargs={'genre': st.session_state.genre_input},
        disabled=st.session_state.genreBox_state
    )

for oid in st.session_state['oid_list']:
    data = st.session_state['data_dict'][oid]
    story = data[0]
    decisionQuestion = data[1]
    chioces = data[2]
    img = data[3]

    generate_content(story, decisionQuestion, chioces, img, oid)