import email
from urllib import response
import streamlit as st
import random 
import time
import openai
from openai import OpenAI
import requests
from mailjet_rest import Client

mailjet_api_key = st.secrets['MAILJET_API_KEY']
mailjet_api_secret = st.secrets['MAILJET_API_SECRET']
mailjet = Client(auth=(mailjet_api_key, mailjet_api_secret))

st.title("Aloo_GPT")

client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])
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
            "parameters": {
                "type": "object",
                "properties": {
                    "FromEmail": {
                        "type": "string",
                        "description": "The email address, eg., alan.learning.acc2@gmail.com",
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
                        "description": "The recipients' email addresses, eg., alan.learning.acc@gmail.com",
                    }

                }cd,
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
        st.markdown(message['content'])


if prompt := st.chat_input('Hello! What can I help you with?'):
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
        
        cont = 'Email has been sent. Check inbox.  \n' + 'Content sent:  \n'+ em['Text-part']
        message_placeholder.markdown(cont)

    st.session_state.messages.append({'role':'assistant','content':cont})
