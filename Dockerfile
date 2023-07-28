# app/Dockerfile

FROM python:3.10.6

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-latex-extra \
    cm-super \
    dvipng \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/dimalbek/MathSensei.git .

COPY requirements.txt .

RUN pip3 install -r requirements.txt
RUN pip3 install latex
RUN pip install matplotlib pillow

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]
