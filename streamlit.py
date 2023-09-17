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
    st.markdown("# Welcome to MathSensei App")
    st.write("MathSensei is a personal math assistant that can help you with various math problems.")

    st.markdown("## Instructions")
    st.write("1. Enter your math problem or question in the input box on the left.")
    st.write("2. Choose the appropriate model: GPT-4 or Wolfram Alpha.")
    st.write(
        "3. Select the appropriate output format: Text and LaTeX or Text (faster option)."
    )
    st.write("3. Click the 'Send' button to get a response from the MathSensei assistant.")
    st.write("4. The assistant will provide an answer or further questions to clarify your query.")
    st.write("5. You can have a conversation with the assistant by entering multiple queries.")

    st.markdown("## About")
    st.write("MathSensei is powered by OpenAI's GPT-4 and Wolfram Alpha.")
    st.write("It aims to provide assistance and solutions to various math problems and queries.")

    st.markdown("## Feedback")
    st.write("We value your feedback! If you have any suggestions or encounter any issues, please provide your feedback using the feedback form.")
    st.write("Your feedback helps us improve the MathSensei app and provide a better user experience.")

    st.markdown("## Примечание")
    st.write(
        "Обратите внимание, что Wolfram Alpha понимает только английский язык, в то время как GPT-4 способен понимать и английский, и русский язык."
    )

    if st.button("Go to main app"):
        st.empty()  # clear content of page
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
    st.set_page_config(page_title="MathSensei", page_icon="🧠")
    st.markdown(
        "<h1 style='text-align: center;'>Your personal Math Sensei🧠</h1>",
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
        model_name = st.sidebar.radio("Choose model:", ("GPT-4", "WolframAlpha"))
        output_format = st.sidebar.radio(
            "Choose output format:",
            ("Text and LaTeX", "Text (faster option)"),
        )
        # counter_placeholder = st.sidebar.empty()
        clear_button = st.sidebar.button("Clear chat", key="clear")

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
            if output_format == "Text and LaTeX":
                st.session_state["bool_latex"] = 1
            else:
                st.session_state["bool_latex"] = 0
            if model_name == "GPT-4":
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
                    chat = openai.ChatCompletion.create(model="gpt-4", messages=msg)
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
                        chat = openai.ChatCompletion.create(model="gpt-4", messages=msg)
                        msg = []
                        yes_nowa = chat.choices[0].message.content
                    except Exception:
                        yes_nowa = "no"
                        over_token = True

                    if yes_nowa.lower() == "yes" or yes_nowa.lower() == "yes.":
                        st.session_state["bool_solve"] = 1

                if over_token is True:
                    answer = "Exception thrown"
                    answer_latex = "Exception thrown"
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
                            model="gpt-4",
                            temperature=0,
                            messages=[{"role": "user", "content": promptt}],
                        )
                        answer = response.choices[0].message.content
                    except Exception:
                        logging.exception("Something went wrong")
                        promptt = f"question: {question}. Please provide VALID and SHORT answer with final result"
                        try:
                            response = openai.ChatCompletion.create(
                                model="gpt-4",
                                temperature=0,
                                messages=[{"role": "user", "content": promptt}],
                            )
                            answer = response.choices[0].message.content
                        except Exception:
                            logging.exception("Too long")
                            answer = "Exception thrown"
                            answer_latex = "Exception thrown"
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
                    answer = "Question is not related to math"
                    answer_latex = "Question is not related to math"
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
                    chat = openai.ChatCompletion.create(model="gpt-4", messages=msg)
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
                                model="gpt-3.5-turbo",
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
                        answer = "I cannot answer to  this question. Try GPT-4 model"
                        answer_latex = "I cannot answer to  this question. Try GPT-4 model"
                        st.session_state["bool_latex"] = 0
                        return (
                            answer,
                            answer_latex,
                        )
                else:
                    answer = "Question is not related to math"
                    answer_latex = "Question is not related to math"
                    st.session_state["bool_latex"] = 0
                    return (
                        answer,
                        answer_latex,
                    )

        # container for chat history
        # response_container = st.container()

        with st.form(key="my_form", clear_on_submit=True):
            user_input = st.text_area("YOU:", key="input", height=100)
            submit_button = st.form_submit_button(label="Send")

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
                if st.session_state["output_format"][i] == "Text and LaTeX":
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
                                model="gpt-4",
                                temperature=0,
                                messages=[
                                    {
                                        "role": "user",
                                        "content": f"Please convert {st.session_state['generated_latex'][i]} to VALID math LaTeX expression and texts formatted inside math VALID LaTeX expression. Example: {latex_example}",
                                    }
                                ],
                            )
                            st.session_state["generated_latex"][i] = response.choices[0].message.content
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
        st.header("Feedback")
        # Star rating component
        rating = st_star_rating(label="", maxValue=5, defaultValue=0, size=30)
        # Feedback form inputs
        email_input = st.text_input("Write you email")
        feedback_text = st.text_area(
            "Please leave your feedback. If you have problems, the task was not solved or you have suggestions to improve the application, describe them here. "
        )

        # Feedback submit button
        if st.button("Send feedback"):
            # Save the feedback and email to a file or database
            save_feedback(email_input, feedback_text, rating)
            st.success("Thanks for feedback!")


# Run the main app
if __name__ == "__main__":
    main_app()
