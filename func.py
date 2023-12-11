import email
from urllib import response
import streamlit as st
import random 
import time
import openai
from openai import OpenAI
import requests
from mailjet_rest import Client


st.sidebar.header('Required API Keys')

#YOU CAN COMMENT THESE THREE LINES WHEN RUNNING LOCALLY AND CAN MAKE USE OF THE secrets.toml FILE TO ADD YOUR API KEYS
mailjet_api_key = st.sidebar.text_input("Enter MailJet API's public key", '', type='password')
mailjet_api_secret = st.sidebar.text_input("Enter MailJet API's private key", '', type='password')
openai_secret_key = st.sidebar.text_input("Enter OpenAI's API key", '', type='password')

#UNCOMMENT THESE LINES WHEN USING THE secret.toml FILE TO ACCESS YOUR API KEYS
#mailjet_api_key = st.secrets['MAILJET_API_KEY']
#mailjet_api_secret = st.secrets['MAILJET_API_SECRET']
#openai_secret_key = st.secrets['OPENAI_API_KEY']

st.title("GPT_Mail")
st.markdown("Can be used only after the API Keys have been entered")

mailjet = Client(auth=(mailjet_api_key, mailjet_api_secret))
client = OpenAI(api_key=openai_secret_key)
GPT_MODEL = 'gpt-3.5-turbo-0613'


def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + st.secrets['OPENAI_API_KEY'],
    }
    json_data = {"model": model, "messages": messages}
    if tools is not None:
        json_data.update({"tools": tools})
    if tool_choice is not None:
        json_data.update({"tool_choice": tool_choice})
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

tools = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email to the specified email with the subject and content",
            "parameters":{
                "type": "object",
                "properties": {
                    "FromEmail": {
                        "type": "string",
                        "description": "The email address, eg., alan.learning.acc@gmail.com",
                    },
                    "FromName": {
                        "type": "string",
                        "description": "The name of the sender, eg., Aloo",
                    },
                    "Subject": {
                        "type": "string",
                        "description": "Subject of the email",
                    },
                    "Text-part": {
                        "type": "string",
                        "description": "The content of the email",
                    },
                    "Recipients": {
                        "type": "string",
                        "description": "The recipients' email addresses",
                    }

                },
                "required": ["FromEmail", "FromName", "Subject", "Text-part", "Recipients"],
            },
        }
    },]


def converter(em):
    em_dict = {}
    names = ['FromEmail','FromName','Subject','Text-part','Recipients']
    for i in range(0,len(em)-1):
        s = em[i].split(':')
        key = names[i]
        value = s[1][2:-2]
        em_dict[key] = value

    s = em[len(em)-1].split(':')
    key = names[len(em)-1]
    value = s[1][2:-1]
    em_dict[key] = [{'Email':value}]
    return em_dict

#code to load previous messages if any
if 'openai_model' not in st.session_state:
    st.session_state['openai_model']="gpt-3.5-turbo"

if 'messages' not in st.session_state:
    st.session_state.messages=[]


for message in st.session_state.messages:
    with st.chat_message(message['role']):
        cont = message['content']
        if message['role']=="assistant":
            cont = 'Email has been sent from '+ cont['FromEmail'] + ' to ' + cont['Recipients'][0]['Email']  + '  \n' + 'Check inbox.  \n' + 'Content sent:  \n'+ cont['Text-part']
        st.markdown(cont)


if prompt := st.chat_input('"Send an email from x to y with the subject as test and content explaining the same"'):
    st.session_state.messages.append({'role':'user','content':prompt})
    with st.chat_message('user'):
        st.markdown(prompt)
    em = ""      
    with st.chat_message('assistant'):
        message_placeholder = st.empty()
        full_response = chat_completion_request([st.session_state.messages[-1]], tools=tools)
        email_format = full_response.json()['choices'][0]['message']['tool_calls'][0]['function']['arguments']

        em = email_format.split('\n')
        em = em[1:-1]
        em = converter(em)

        result = mailjet.send.create(data=em)
        
        
        cont = 'Email has been sent from '+ em['FromEmail'] + ' to ' + em['Recipients'][0]['Email']  + '  \n' + 'Check inbox.  \n' + 'Content sent:  \n'+ em['Text-part']
        
        message_placeholder.markdown(cont)

    st.session_state.messages.append({'role':'assistant','content':em})
