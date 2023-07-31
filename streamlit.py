import openai
import wolframalpha
import streamlit as st
from streamlit_chat import message
import pymongo
import logging
from bson.objectid import ObjectId
from streamlit_star_rating import st_star_rating
import matplotlib.pyplot as plt
import io
import os


def home_page():
    st.markdown("# Добро пожаловать в приложение MathSensei")
    st.write(
        "MathSensei - это персональный математический помощник, который поможет вам решить различные математические проблемы."
    )

    st.markdown("## Инструкции")
    st.write("1. Введите вашу математическую задачу или вопрос в поле ввода.")
    st.write("2. Выберите подходящую модель: GPT-3.5 или Wolfram Alpha.")
    st.write(
        "3. Нажмите кнопку 'Отправить', чтобы получить ответ от помощника MathSensei."
    )
    st.write(
        "4. Помощник предоставит ответ или дополнительные вопросы для уточнения вашего запроса."
    )
    st.write(
        "5. Вы можете вести диалог с помощником, задавая несколько запросов подряд."
    )

    st.markdown("## О приложении")
    st.write("MathSensei работает на базе GPT-3.5 от OpenAI и Wolfram Alpha.")
    st.write(
        "Он призван помочь с решением различных математических проблем и вопросов."
    )

    st.markdown("## Обратная связь")
    st.write(
        "Мы ценим ваше мнение! Если у вас есть предложения или возникли проблемы, пожалуйста, оставьте свой отзыв, используя форму обратной связи."
    )
    st.write(
        "Ваш отзыв помогает нам улучшить приложение MathSensei и предоставить лучший пользовательский опыт."
    )

    st.markdown("## Примечание")
    st.write(
        "Обратите внимание, что Wolfram Alpha понимает только английский язык, в то время как GPT-3.5 способен понимать и английский, и русский язык."
    )

    if st.button("Перейти к основному приложению"):
        st.empty()  # Очистить содержимое домашней страницы
        main_app()


def get_db_client():
    mongo_url = os.getenv("MONGO_URL")
    if not mongo_url:
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
        openai_org_id = os.getenv("OPENAI_ORG_ID")
        if not openai_org_id:
            openai_org_id = st.secrets["OPENAI_ORG_ID"]
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            openai_api_key = st.secrets["OPENAI_API_KEY"]
        wolframalpha_app_id = os.getenv("WOLFRAMALPHA_APP_ID")
        if not wolframalpha_app_id:
            wolframalpha_app_id = st.secrets["WOLFRAMALPHA_APP_ID"]

        openai.organization = openai_org_id
        openai.api_key = openai_api_key
        wa_client = wolframalpha.Client(wolframalpha_app_id)

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

        if "history" not in st.session_state:
            st.session_state["history"] = []
        if "bool_solve" not in st.session_state:
            st.session_state["bool_solve"] = 0
        if "generated_latex" not in st.session_state:
            st.session_state["generated_latex"] = []
        if "output_format" not in st.session_state:
            st.session_state["output_format"] = []
        if "print_latex" not in st.session_state:
            st.session_state["bool_latex"] = 1

        # Sidebar - let user choose model, output format, and let user clear the current conversation
        st.sidebar.title("Math Sensei")
        model_name = st.sidebar.radio("Выберите модель:", ("GPT-3.5", "wolframalpha"))
        output_format = st.sidebar.radio(
            "Выберите формат вывода:", ("Текст и LaTeX", "Текст (более быстрый вариант)")
        )
        # counter_placeholder = st.sidebar.empty()
        clear_button = st.sidebar.button("Очистить чат", key="clear")

        def clear():
            st.session_state["generated"] = []
            st.session_state["past"] = []
            st.session_state["messages"] = [
                {"role": "system", "content": "You are a helpful assistant."}
            ]
            st.session_state["model_name"] = []
            st.session_state["bool_solve"] = 0
            st.session_state["generated_latex"] = []
            st.session_state["bool_latex"] = 1
            st.session_state["ouput_format"] = []

        # reset everything
        if clear_button:
            clear()

        # generate a response
        def generate_response(prompt):
            if output_format == "Текст и LaTeX":
                st.session_state["bool_latex"] = 1
            else:
                st.session_state["bool_latex"] = 0
            if model_name == "GPT-3.5":
                question = prompt
                over_token = False
                msg = []

                st.session_state["messages"].append(
                    {"role": "user", "content": question}
                )

                msg.append(
                    {
                        "role": "assistant",
                        "content": f"{question} is this a math problem? (answer only yes or no)",
                    }
                )
                try:
                    chat = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo", messages=msg
                    )
                    msg = []
                    yes_no = chat.choices[0].message.content
                except Exception:
                    yes_no = "no"
                    over_token = True

                if st.session_state["past"] and (
                    yes_no.lower() == "no" or yes_no.lower() == "no."
                ):
                    msg.append(
                        {
                            "role": "assistant",
                            "content": f'is {question} related to {st.session_state["past"][-1]} or {st.session_state["generated"][-1]}? (answer only yes or no)',
                        }
                    )
                    try:
                        chat = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo", messages=msg
                        )
                        msg = []
                        yes_nowa = chat.choices[0].message.content
                    except Exception:
                        yes_nowa = "no"
                        over_token = True

                    if yes_nowa.lower() == "yes" or yes_nowa.lower() == "yes.":
                        st.session_state["bool_solve"] = 1
                
                if over_token is True:
                    answer = "Длина вопроса слишком большая"
                    answer_latex = "Длина вопроса слишком большая"
                    st.session_state["bool_latex"] = 0
                    st.session_state["messages"].append(
                        {"role": "assistant", "content": answer}
                    )
                    return (
                        answer,
                        answer_latex,
                    )
                if (
                    yes_no.lower() == "yes"
                    or yes_no.lower() == "yes."
                    or st.session_state["bool_solve"] == 1
                ):
                    if st.session_state["past"]:
                        last_past = st.session_state["past"][-1]
                    else:
                        last_past = ""

                    if st.session_state["generated"]:
                        last_generated = st.session_state["generated"][-1]
                    else:
                        last_generated = ""

                    promptt = f"question: {last_past}, answer: {last_generated}. question: {question}. Please provide VALID and SHORT answer with final result"

                    try:
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            temperature=0,
                            messages=[{"role": "user", "content": promptt}],
                        )
                        answer = response.choices[0].message.content
                    except Exception:
                        logging.exception("Something went wrong")
                        promptt = f"question: {question}. Please provide VALID and SHORT answer with final result"
                        try:
                            response = openai.ChatCompletion.create(
                                model="gpt-3.5-turbo",
                                temperature=0,
                                messages=[{"role": "user", "content": promptt}],
                            )
                            answer = response.choices[0].message.content
                        except Exception:
                            logging.exception("Too long")
                            answer = "Длина вопроса слишком большая"
                            answer_latex = "Длина вопроса слишком большая"
                            st.session_state["bool_latex"] = 0
                            st.session_state["messages"].append(
                                {"role": "assistant", "content": answer}
                            )
                            return (
                                answer,
                                answer_latex,
                            )
                    print(
                        f'\n\n\nPAST: {last_past}\nGENERATED {last_generated}\nMESSAGES {st.session_state["messages"][-1]}\n\n'
                    )
                    if st.session_state["bool_latex"] == 1:
                        latex_example = "$A = 2\pi \int_{a}^{b} y \sqrt{1 + \left(\frac{dy}{dx}\right)^2} \, dx$"
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            temperature=0,
                            messages=[
                                {
                                    "role": "user",
                                    "content": f"Please convert {answer} to VALID math LaTeX expression and texts formatted inside math VALID LaTeX expression. Example: {latex_example}. Do not answer such as 'VALID math LaTeX expression is ... and texts formatted inside math VALID LaTeX expression is...'",
                                }
                            ],
                        )
                        answer_latex = response.choices[0].message.content
                    else:
                        answer_latex = ""

                    return (
                        answer,
                        answer_latex,
                    )

                else:
                    answer = "Данный вопрос не относится к математике, поэтому я не могу предоставить ответ на него"
                    answer_latex = "Данный вопрос не относится к математике, поэтому я не могу предоставить ответ на него"
                    st.session_state["bool_latex"] = 0
                    return (
                        answer,
                        answer_latex,
                    )

            else:
                problem = prompt
                over_token = False
                st.session_state["messages"].append(
                    {"role": "user", "content": problem}
                )
                msg = []
                msg.append(
                    {
                        "role": "assistant",
                        "content": f"{problem} is this a math problem? (answer only yes or no)",
                    }
                )

                try:
                    chat = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo", messages=msg
                    )
                    yes_no = chat.choices[0].message.content
                except Exception:
                    over_token = True
                    yes_no = "no"
                    st.session_state["bool_latex"] = 0
                
                msg = []
                if yes_no.lower() == "yes" or yes_no.lower() == "yes.":
                    try:
                        wa_res = wa_client.query(problem)
                        answer = next(wa_res.results).text
                        if st.session_state["bool_latex"] == 1:
                            latex_example = "$A = 2\pi \int_{a}^{b} y \sqrt{1 + \left(\frac{dy}{dx}\right)^2} \, dx$"
                            response = openai.ChatCompletion.create(
                                model="gpt-3.5-turbo-16k",
                                temperature=0,
                                messages=[
                                    {
                                        "role": "user",
                                        "content": f"Please convert {answer} to VALID math LaTeX expression and texts formatted inside math VALID LaTeX expression. Example: {latex_example}",
                                    }
                                ],
                            )
                            answer_latex = response.choices[0].message.content
                        else:
                            answer_latex = ""
                        return (
                            answer,
                            answer_latex,
                        )
                    except Exception:
                        answer = "Извините, я не могу предоставить ответ на данную задачу. Попробуйте модель GPT-3.5"
                        answer_latex = "Извините, я не могу предоставить ответ на данную задачу. Попробуйте модель GPT-3.5"
                        st.session_state["bool_latex"] = 0
                        return (
                            answer,
                            answer_latex,
                        )
                else:
                    answer = "Данный вопрос не относится к математике, поэтому я не могу предоставить ответ на него"
                    answer_latex = "Данный вопрос не относится к математике, поэтому я не могу предоставить ответ на него"
                    st.session_state["bool_latex"] = 0
                    return (
                        answer,
                        answer_latex,
                    )

        # container for chat history
        # response_container = st.container()

        with st.form(key="my_form", clear_on_submit=True):
            user_input = st.text_area("ВЫ:", key="input", height=100)
            submit_button = st.form_submit_button(label="Отправить")

        if submit_button and user_input:
            (
                output,
                latex_output,
            ) = generate_response(user_input)

            print(output)

            st.session_state["past"].append(user_input)
            st.session_state["generated"].append(output)
            st.session_state["generated_latex"].append(latex_output)
            st.session_state["model_name"].append(model_name)
            st.session_state["output_format"].append(output_format)

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

        if st.session_state["generated"]:
            # with response_container:
            for i in range(len(st.session_state["generated"])):
                message(
                    st.session_state["past"][i],
                    is_user=True,
                    key=str(i) + "_user",
                    avatar_style="micah",
                )

                message(
                    st.session_state["generated"][i],
                    key=str(i),
                    avatar_style="identicon",
                )

                # Render the LaTeX equation as an image using matplotlib
                if st.session_state["output_format"][i] == "Текст и LaTeX":
                    try:
                        fig, ax = plt.subplots()
                        ax.text(
                            0.01,
                            0.5,
                            st.session_state["generated_latex"][i],
                            fontsize=20,
                            usetex=True,
                        )
                        ax.axis("off")
                        buffer = io.BytesIO()
                        plt.savefig(
                            buffer,
                            format="png",
                            dpi=450,
                            bbox_inches="tight",
                            pad_inches=0.0,
                            transparent=True,
                        )
                        plt.close(fig)

                        # Display the image in the Streamlit app
                        st.image(buffer.getvalue())

                    except Exception:
                        try:
                            latex_example = "$A = 2\pi \int_{a}^{b} y \sqrt{1 + \left(\frac{dy}{dx}\right)^2} \, dx$"
                            response = openai.ChatCompletion.create(
                                model="gpt-3.5-turbo",
                                temperature=0,
                                messages=[
                                    {
                                        "role": "user",
                                        "content": f"Please convert {latex_output} to VALID math LaTeX expression and texts formatted inside math VALID LaTeX expression. Example: {latex_example}",
                                    }
                                ],
                            )
                            latex_output = response.choices[0].message.content
                            fig, ax = plt.subplots()
                            ax.text(
                                0.01,
                                0.5,
                                st.session_state["generated_latex"][i],
                                fontsize=20,
                                usetex=True,
                            )
                            ax.axis("off")
                            buffer = io.BytesIO()
                            plt.savefig(
                                buffer,
                                format="png",
                                dpi=450,
                                bbox_inches="tight",
                                pad_inches=0.0,
                                transparent=True,
                            )
                            plt.close(fig)

                            # Display the image in the Streamlit app
                            st.image(buffer.getvalue())
                        except Exception:
                            logging.exception("latex incorrect")

                st.write(f"Используемая модель: {st.session_state['model_name'][i]}")

        def save_feedback(email, feedback, rating):
            # Save the feedback, rating and email to MongoDB
            feedback_data = {"email": email, "rating": rating, "feedback": feedback}
            db["feedbacks"].insert_one(feedback_data)

        # with feedback_container:
        st.header("Обратная связь")
        # Star rating component
        rating = st_star_rating(label="", maxValue=5, defaultValue=0, size=30)
        # Feedback form inputs
        email_input = st.text_input("Введите ваш адрес электронной почты")
        feedback_text = st.text_area(
            "Пожалуйста, оставьте ваш отзыв. Если у вас возникли проблемы, задача не была решена или у вас есть предложения по улучшению приложения, опишите их здесь. "
        )

        # Feedback submit button
        if st.button("Отправить обратную связь"):
            # Save the feedback and email to a file or database
            save_feedback(email_input, feedback_text, rating)
            st.success("Спасибо за ваш отзыв!")


# Run the main app
if __name__ == "__main__":
    main_app()
