import openai
import wolframalpha
import streamlit as st
from streamlit_chat import message
import pymongo
from bson.objectid import ObjectId
from streamlit_star_rating import st_star_rating


def home_page():
    st.markdown("# Добро пожаловать в приложение MathSensei")
    st.write("MathSensei - это персональный математический помощник, который поможет вам решить различные математические проблемы.")

    st.markdown("## Инструкции")
    st.write("1. Введите вашу математическую задачу или вопрос в поле ввода.")
    st.write("2. Выберите подходящую модель: GPT-3.5 или Wolfram Alpha.")
    st.write("3. Нажмите кнопку 'Отправить', чтобы получить ответ от помощника MathSensei.")
    st.write("4. Помощник предоставит ответ или дополнительные вопросы для уточнения вашего запроса.")
    st.write("5. Вы можете вести диалог с помощником, задавая несколько запросов подряд.")

    st.markdown("## О приложении")
    st.write("MathSensei работает на базе GPT-3.5 от OpenAI и Wolfram Alpha.")
    st.write("Он призван помочь с решением различных математических проблем и вопросов.")

    st.markdown("## Обратная связь")
    st.write("Мы ценим ваше мнение! Если у вас есть предложения или возникли проблемы, пожалуйста, оставьте свой отзыв, используя форму обратной связи.")
    st.write("Ваш отзыв помогает нам улучшить приложение MathSensei и предоставить лучший пользовательский опыт.")

    st.markdown("## Примечание")
    st.write("Обратите внимание, что Wolfram Alpha понимает только английский язык, в то время как GPT-3.5 способен понимать и английский, и русский язык.")
    
    if st.button("Перейти к основному приложению"):
        st.empty()  # Очистить содержимое домашней страницы
        main_app()


def get_db_client():
    mongo_url = st.secrets["MONGO_URL"]

    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = pymongo.MongoClient(mongo_url)
    return client


client = get_db_client()
db = client.mathsensei


def main_app():
    # Setting page title and header
    st.set_page_config(page_title="MathSensei", page_icon=":robot_face:")
    st.markdown(
        "<h1 style='text-align: center;'>Твой личный Math Sensei🧠</h1>",
        unsafe_allow_html=True,
    )

    # Check if it's the first visit
    if "visited" not in st.session_state:
        st.session_state.visited = True
        # Show the home page
        home_page()
    else:

        # Set org ID and API key
        openai.organization = st.secrets["OPENAI_ORG_ID"]
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        wa_client = wolframalpha.Client(st.secrets["WOLFRAMALPHA_APP_ID"])

        # Initialise session state variables
        if "generated" not in st.session_state:
            st.session_state["generated"] = []
        if "past" not in st.session_state:
            st.session_state["past"] = []
        if "messages" not in st.session_state:
            st.session_state["messages"] = [
                {"role": "system", "content": "You are a helpful assistant."}
            ]
        if "model_name" not in st.session_state:
            st.session_state["model_name"] = []
        if "cost" not in st.session_state:
            st.session_state["cost"] = []
        if "total_tokens" not in st.session_state:
            st.session_state["total_tokens"] = []
        if "total_cost" not in st.session_state:
            st.session_state["total_cost"] = 0.0

        if "history" not in st.session_state:
            st.session_state["history"] = []
        if "bool_solve" not in st.session_state:
            st.session_state["bool_solve"] = 0

        # Sidebar - let user choose model, show total cost of current conversation, and let user clear the current conversation
        st.sidebar.title("Math Sensei")
        model_name = st.sidebar.radio("Выберите модель:", ("GPT-3.5", "wolframalpha"))
        counter_placeholder = st.sidebar.empty()
        counter_placeholder.write(
            f"Общая сумма разговора: ${st.session_state['total_cost']:.5f}"
        )
        clear_button = st.sidebar.button("Очистить чат", key="clear")

        def clear():
            st.session_state["generated"] = []
            st.session_state["past"] = []
            st.session_state["messages"] = [
                {"role": "system", "content": "You are a helpful assistant."}
            ]
            st.session_state["number_tokens"] = []
            st.session_state["model_name"] = []
            st.session_state["cost"] = []
            st.session_state["total_cost"] = 0.0
            st.session_state["total_tokens"] = []
            st.session_state["bool_solve"] = 0

            counter_placeholder.write(
                f"Общая сумма разговора: ${st.session_state['total_cost']:.5f}"
            )

        # reset everything
        if clear_button:
            clear()

        # generate a response
        def generate_response(prompt):
            if model_name == "GPT-3.5":
                question = prompt
                if st.session_state["past"]:
                    st.session_state["messages"].append({"role": "user", "content": question})
                    st.session_state["messages"].append(
                        {
                            "role": "assistant",
                            "content": f'is {question} related to {st.session_state["past"][-1]} or {st.session_state["generated"][-1]}? (answer only yes or no)',
                        }
                    )

                    chat = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo", messages=st.session_state["messages"]
                    )
                    reply = chat.choices[0].message.content
                    yes_nowa = reply
                    st.session_state["messages"].append({"role": "assistant", "content": reply})
                    if yes_nowa.lower() == "yes" or yes_nowa.lower() == "yes.":
                        st.session_state["bool_solve"] = 1

                st.session_state["messages"].append({"role": "user", "content": question})
                st.session_state["messages"].append(
                    {
                        "role": "assistant",
                        "content": f"{question} is this a math problem? (answer only yes or no)",
                    }
                )
                chat = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=st.session_state["messages"]
                )
                reply = chat.choices[0].message.content
                yes_no = reply
                st.session_state["messages"].append({"role": "assistant", "content": reply})

                if yes_no.lower() == "yes" or yes_no.lower() == "yes." or st.session_state["bool_solve"] == 1:
                    if st.session_state["past"]:
                        last_past = st.session_state["past"][-1]
                    else:
                        last_past = ""

                    if st.session_state["generated"]:
                        last_generated = st.session_state["generated"][-1]
                    else:
                        last_generated = ""

                    promptt = f"question: {last_past}, answer: {last_generated}. {question}"

                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        temperature=0,
                        messages=[{"role": "user", "content": promptt}],
                    )
                    print(
                        f'\n\n\nPAST: {last_past}\nGENERATED {last_generated}\nMESSAGES {st.session_state["messages"][-1]}\n\n'
                    )
                    answer = response.choices[0].message.content

                    total_tokens = response.usage.total_tokens
                    prompt_tokens = response.usage.prompt_tokens
                    completion_tokens = response.usage.completion_tokens
                    return answer, total_tokens, prompt_tokens, completion_tokens

                else:
                    total_tokens = st.session_state["total_cost"]
                    prompt_tokens = 0
                    completion_tokens = 0
                    answer = "Данный вопрос не относится к математике, поэтому я не могу предоставить ответ на него"
                    return answer, total_tokens, prompt_tokens, completion_tokens
                
            else:
                problem = prompt
                st.session_state["messages"].append({"role": "user", "content": problem})
                st.session_state["messages"].append(
                    {
                        "role": "assistant",
                        "content": f"{problem} is this a math problem? (answer only yes or no)",
                    }
                )
                chat = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=st.session_state["messages"]
                )
                reply = chat.choices[0].message.content
                yes_no = reply
                st.session_state["messages"].append({"role": "assistant", "content": reply})
                if yes_no.lower() == "yes" or yes_no.lower() == "yes.":
                    try:
                        wa_res = wa_client.query(problem)
                        answer = next(wa_res.results).text

                        total_tokens = st.session_state["total_cost"]
                        prompt_tokens = 0
                        completion_tokens = 0
                        print(answer)
                        return answer, total_tokens, prompt_tokens, completion_tokens
                    except Exception:
                        total_tokens = st.session_state["total_cost"]
                        prompt_tokens = 0
                        completion_tokens = 0
                        answer = "Извините, я не могу предоставить ответ на данную задачу. Попробуйте модель GPT-3.5"
                        return answer, total_tokens, prompt_tokens, completion_tokens
                else:
                    total_tokens = st.session_state["total_cost"]
                    prompt_tokens = 0
                    completion_tokens = 0
                    answer = "Данный вопрос не относится к математике, поэтому я не могу предоставить ответ на него"
                    return answer, total_tokens, prompt_tokens, completion_tokens

        # container for chat history
        response_container = st.container()
        # container for text box
        container = st.container()

        with container:
            with st.form(key="my_form", clear_on_submit=True):
                user_input = st.text_area("ВЫ:", key="input", height=100)
                submit_button = st.form_submit_button(label="Отправить")

            if submit_button and user_input:
                output, total_tokens, prompt_tokens, completion_tokens = generate_response(
                    user_input
                )
                st.session_state["past"].append(user_input)
                st.session_state["generated"].append(output)
                st.session_state["model_name"].append(model_name)
                st.session_state["total_tokens"].append(total_tokens)

                st.session_state["history"].append(user_input)
                st.session_state["history"].append(output)

                if "conversation_id" not in st.session_state:
                    conversation_data = db["conversations"].insert_one(
                        {"history": st.session_state["history"]}
                    )
                    conversation_id = conversation_data.inserted_id
                    st.session_state.conversation_id = conversation_id
                else:
                    db["conversations"].update_one(
                        filter={"_id": ObjectId(st.session_state.conversation_id)},
                        update={
                            "$set": {"history": st.session_state["history"]},
                        },
                    )

                # from https://openai.com/pricing#language-models
                if model_name == "GPT-3.5":
                    cost = total_tokens * 0.002 / 1000

                if model_name == "GPT-3.5":
                    st.session_state["cost"].append(cost)
                    st.session_state["total_cost"] += cost

        if st.session_state["generated"]:
            with response_container:
                for i in range(len(st.session_state["generated"])):
                    message(
                        st.session_state["past"][i],
                        is_user=True,
                        key=str(i) + "_user",
                        avatar_style="micah",
                    )
                    message(
                        st.session_state["generated"][i], key=str(i), avatar_style="identicon"
                    )
                    if model_name == "GPT-3.5":
                        # st.write(
                        #     str(st.session_state)
                        #     + "Index:"
                        #     + str(i)
                        # )
                        if i != 0:
                            st.write(
                                f"Используемая модель: {st.session_state['model_name'][i]}; Количество токенов: {st.session_state['total_tokens'][i]}; Цена: ${st.session_state['cost'][0]:.5f}"
                            )
                    else:
                        st.write(
                            f"Используемая модель: {st.session_state['model_name'][i]}; Количество токенов: {st.session_state['total_tokens'][i]}"
                        )
                    counter_placeholder.write(
                        f"Общая сумма разговора: ${st.session_state['total_cost']:.5f}"
                    )

        def save_feedback(email, feedback, rating):
            # Save the feedback, rating and email to MongoDB
            feedback_data = {
                "email": email,
                "rating": rating,
                "feedback": feedback
            }
            db["feedbacks"].insert_one(feedback_data)

        # container for feedback form
        feedback_container = st.container()

        with feedback_container:
            st.header("Обратная связь")
            # Star rating component
            rating = st_star_rating(
                        label="", maxValue=5, defaultValue=0, size=30
                    )
            # Feedback form inputs
            email_input = st.text_input("Введите ваш адрес электронной почты")
            feedback_text = st.text_area("Пожалуйста, оставьте ваш отзыв. Если у вас возникли проблемы, задача не была решена или у вас есть предложения по улучшению приложения, опишите их здесь. ")

            # Feedback submit button
            if st.button("Отправить обратную связь"):
                # Save the feedback and email to a file or database
                save_feedback(email_input, feedback_text, rating)
                st.success("Спасибо за ваш отзыв!")

        print("DB STATS:")
        print(db.command("dbStats"))


# Run the main app
if __name__ == "__main__":
    main_app()