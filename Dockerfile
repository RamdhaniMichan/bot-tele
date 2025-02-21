FROM python:3.10

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

ENV GOOGLE_CRED="/app/credentials.json"
ENV SPREADSHEET_ID=1yac8ha4H9zDRQy7hv2GJ-myIWXWT2H9c_XL7R7YvRa4
ENV TELE_BOT=8094586161:AAE00XnDQJL6WL6Ml2C7J_fp9EXWMXJI_XE

CMD ["python", "bot.py"]
