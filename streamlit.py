import openai
import os
import wolframalpha
import streamlit as st
from streamlit_chat import message
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain.llms import OpenAI
from langchain.chains import ConversationChain

load_dotenv()

# Setting page title and header
st.set_page_config(page_title="MathSensei", page_icon=":robot_face:")
st.markdown("<h1 style='text-align: center;'>Your personal Math Sensei🧠</h1>", unsafe_allow_html=True)

# Set org ID and API key
openai.organization = os.getenv("OPENAI_ORG_ID")
openai.api_key = os.getenv("OPENAI_API_KEY")
wa_client = wolframalpha.Client(os.getenv("WOLFRAMALPHA_APP_ID"))

# initialize memory
memory = ConversationBufferMemory()

# llm = OpenAI(temperature=0, model='gpt-3.5-turbo')
# conversation = ConversationChain(
#     llm=llm,
#     verbose=True,
#     memory=memory)


# Initialise session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
if 'model_name' not in st.session_state:
    st.session_state['model_name'] = []
if 'cost' not in st.session_state:
    st.session_state['cost'] = []
if 'total_tokens' not in st.session_state:
    st.session_state['total_tokens'] = []
if 'total_cost' not in st.session_state:
    st.session_state['total_cost'] = 0.0

# Sidebar - let user choose model, show total cost of current conversation, and let user clear the current conversation
st.sidebar.title("Math Sensei")
model_name = st.sidebar.radio("Choose a model:", ("GPT-3.5", "wolframalpha"))
counter_placeholder = st.sidebar.empty()
counter_placeholder.write(f"Total cost of this conversation: ${st.session_state['total_cost']:.5f}")
clear_button = st.sidebar.button("Clear Conversation", key="clear")

# Map model names to OpenAI model IDs
if model_name == "GPT-3.5":
    model = "gpt-3.5-turbo"
else:
    model = "wolframalpha"

def clear():
    st.session_state['generated'] = []
    st.session_state['past'] = []
    st.session_state['messages'] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
    st.session_state['number_tokens'] = []
    st.session_state['model_name'] = []
    st.session_state['cost'] = []
    st.session_state['total_cost'] = 0.0
    st.session_state['total_tokens'] = []

    global boool, boool2
    boool = 0
    boool2 = 0
    counter_placeholder.write(f"Total cost of this conversation: ${st.session_state['total_cost']:.5f}")


# reset everything
if clear_button:
    clear()

last_question = None
last_answer = None
boool = 0
boool2 = 0


# generate a response
def generate_response(prompt):
    # clear()
    global boool
    global boool2
    global last_answer
    global last_question
    if model_name == "GPT-3.5":
        question = prompt
        #buffer memory
        memory.chat_memory.add_user_message(question)

        st.session_state['messages'].append({"role": "user", "content": question})
        st.session_state['messages'].append({"role": "assistant", "content": f'{question} is this a math problem? (answer only yes or no)'}) 
        chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=st.session_state['messages'])
        reply = chat.choices[0].message.content
        yes_no = reply
        st.session_state['messages'].append({"role": "assistant", "content": reply})
        if boool == 1:
            # st.session_state['messages'].clear
            st.session_state['messages'].append({"role": "user", "content": question})
            # st.session_state['messages'].append({"role": "assistant", "content": f'is {question} related to {last_question} or {last_answer}? (answer only yes or no)'})
            st.session_state['messages'].append({"role": "assistant", "content": f'is {question} related to {st.session_state["past"]} or {st.session_state["generated"]}? (answer only yes or no)'})

            chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=st.session_state['messages'])
            reply = chat.choices[0].message.content
            yes_nowa = reply
            st.session_state['messages'].append({"role": "assistant", "content": reply})
            if yes_nowa.lower() == 'yes' or yes_nowa.lower() == 'yes.':
                boool2 = 1

        if yes_no.lower() == 'yes' or yes_no.lower() == 'yes.' or boool2 == 1:
            # promptt = f"question: {last_question}, answer: {last_answer}. {question}"
            promptt = f"question: {st.session_state['past']}, answer: {st.session_state['generated']}. {question}"            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                temperature=0,
                messages=[{"role": "user", "content": promptt}],
            )
            # llm = OpenAI(temperature=0)
            # conversation = ConversationChain(
            #     llm=llm,
            #     verbose=True,
            #     memory=memory)
            # global conversation
            # answer = conversation.predict(input=question)
            answer = response.choices[0].message.content
            last_question = question
            last_answer = answer
            boool = 1

            #buffer memory
            memory.chat_memory.add_ai_message(answer)
            memory.load_memory_variables({})
            # print(memory.dict())

            # print(st.session_state['messages'])
            total_tokens = response.usage.total_tokens
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            # print(answer)
            return answer, total_tokens, prompt_tokens, completion_tokens
            # return answer, 0, 0, 0
        
        else:
            total_tokens = st.session_state['total_cost']
            prompt_tokens = 0
            completion_tokens = 0
            answer = "I'm a math assistant and I can only solve math problems. The problem you provided is not related to math"
            return answer, total_tokens, prompt_tokens, completion_tokens
        
        # st.session_state['messages'].append({"role": "user", "content": prompt})

        # completion = openai.ChatCompletion.create(
        #     model=model,
        #     messages=st.session_state['messages']
        # )
        # response = completion.choices[0].message.content
        # st.session_state['messages'].append({"role": "assistant", "content": response})
        # # print(st.session_state['messages'])
        # total_tokens = completion.usage.total_tokens
        # prompt_tokens = completion.usage.prompt_tokens
        # completion_tokens = completion.usage.completion_tokens
        # return response, total_tokens, prompt_tokens, completion_tokens
    else:
        problem = prompt
        st.session_state['messages'].append({"role": "user", "content": problem})
        st.session_state['messages'].append({"role": "assistant", "content": f'{problem} is this a math problem? (answer only yes or no)'}) 
        chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=st.session_state['messages'])
        reply = chat.choices[0].message.content
        yes_no = reply
        st.session_state['messages'].append({"role": "assistant", "content": reply})
        if yes_no.lower() == 'yes' or yes_no.lower() == 'yes.':
            # global boool
            boool = 1
            # global last_question
            last_question = problem

            try:
                wa_res = wa_client.query(problem)
                answer = next(wa_res.results).text
                
                # buffer memory
                memory.chat_memory.add_user_message(problem)
                memory.chat_memory.add_ai_message(answer)
                memory.load_memory_variables({})

                # global last_answer
                last_answer = answer
                total_tokens = st.session_state['total_cost']
                prompt_tokens = 0
                completion_tokens = 0
                print(answer)
                return answer, total_tokens, prompt_tokens, completion_tokens
            except Exception:
                total_tokens = st.session_state['total_cost']
                prompt_tokens = 0
                completion_tokens = 0
                answer = "I'm sorry, I couldn't solve the problem."
                return answer, total_tokens, prompt_tokens, completion_tokens
        else:
            total_tokens = st.session_state['total_cost']
            prompt_tokens = 0
            completion_tokens = 0
            answer = "I'm a math assistant and I can only solve math problems. The problem you provided is not related to math"
            return answer, total_tokens, prompt_tokens, completion_tokens


# container for chat history
response_container = st.container()
# container for text box
container = st.container()

with container:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("You:", key='input', height=100)
        submit_button = st.form_submit_button(label='Send')

    if submit_button and user_input:
        output, total_tokens, prompt_tokens, completion_tokens = generate_response(user_input)
        st.session_state['past'].append(user_input)
        st.session_state['generated'].append(output)
        st.session_state['model_name'].append(model_name)
        st.session_state['total_tokens'].append(total_tokens)

        # from https://openai.com/pricing#language-models
        if model_name == "GPT-3.5":
            cost = total_tokens * 0.002 / 1000
        # else:
        #     cost = (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000
        if model_name == "GPT-3.5":
            st.session_state['cost'].append(cost)
            st.session_state['total_cost'] += cost

if st.session_state['generated']:
    with response_container:
        for i in range(len(st.session_state['generated'])):
            message(st.session_state["past"][i], is_user=True, key=str(i) + '_user', avatar_style='micah')
            message(st.session_state["generated"][i], key=str(i), avatar_style='identicon')
            if model_name == "GPT-3.5":
                st.write(
                    f"Model used: {st.session_state['model_name'][i]}; Number of tokens: {st.session_state['total_tokens'][i]}; Cost: ${st.session_state['cost'][i]:.5f}")
            else:
                st.write(
                    f"Model used: {st.session_state['model_name'][i]}; Number of tokens: {st.session_state['total_tokens'][i]}")
            counter_placeholder.write(f"Total cost of this conversation: ${st.session_state['total_cost']:.5f}")
