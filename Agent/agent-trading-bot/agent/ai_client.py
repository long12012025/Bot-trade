import os
import time
import logging
import openai
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='agent_ai_client.log',
    filemode='a'
)

class AIClient:
    def __init__(self, model="gpt-4", temperature=0.7, max_tokens=300, max_retries=3):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if openai.api_key is None:
            raise ValueError("OPENAI_API_KEY chưa được thiết lập trong biến môi trường.")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries

    def get_strategy(self, prompt: str) -> str:
        retries = 0
        while retries < self.max_retries:
            try:
                logging.info(f"Gửi prompt tới API: {prompt}")
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a smart trading assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                strategy = response.choices[0].message.content.strip()
                logging.info(f"Nhận phản hồi: {strategy}")
                return strategy
            except Exception as e:
                retries += 1
                logging.error(f"Lỗi API: {e}, thử lại lần {retries}")
                time.sleep(2 ** retries)
        logging.error("Không thể lấy chiến lược do lỗi API sau nhiều lần thử.")
        return "Không thể lấy chiến lược do lỗi API sau nhiều lần thử."
