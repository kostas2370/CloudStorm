from openai.types.beta.threads.message_create_params import (
    Attachment,
    AttachmentToolFileSearch,
)
import base64
from openai import OpenAI
from django.conf import settings
import io

from .transcribe_utils import speech_to_text, video_to_text


def document_data_extraction(file, prompt):
    client = OpenAI(api_key = settings.OPEN_API_KEY)
    cloudstorm_assistant = client.beta.assistants.create(
        model="gpt-4o",
        name="Cloudstorm assistant",
        instructions="You are a file assistant chatbot. When asked a question, answer from the uploaded file.",
        tools=[{"type": "file_search"}],
        )
    thread = client.beta.threads.create()
    extracted_data = file.extracted_data.filter(name = "open_ai_file_id").first()

    if not extracted_data:
        with file.file.open("rb") as f:
            openai_file = client.files.create(file = (file.file.name, f), purpose = "user_data")
            extracted_data = file.create_extracted_data(name = "open_ai_file_id", data = openai_file.id,
                                                        hidden_from_user = True)

    client.beta.threads.messages.create(thread_id = thread.id, role = "user",
                                        attachments = [Attachment(file_id = extracted_data.data,
                                                                  tools = [AttachmentToolFileSearch(type = "file_search")])],
                                        content = prompt, )

    run = client.beta.threads.runs.create_and_poll(thread_id = thread.id, assistant_id = cloudstorm_assistant.id,
                                                   timeout = 1000)
    if run.status != "completed":
        raise Exception("Run failed:", run.status)

    messages_cursor = client.beta.threads.messages.list(thread_id=thread.id)
    messages = [message for message in messages_cursor]

    res_txt = messages[0].content[0].text.value

    return res_txt


def image_data_extraction(file, prompt: str) -> str:
    client = OpenAI(api_key = settings.OPEN_API_KEY)
    with file.file.open() as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{file.file_extension};base64,{encoded_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        max_tokens=500,

    )

    return response.choices[0].message.content


def string_data_extraction(string, prompt):
    x = io.StringIO()
    client = OpenAI(api_key = settings.OPEN_API_KEY)
    gpt_prompt = f"Given the following text: {string}, perform the following task: {prompt}"

    stream = client.chat.completions.create(model = "gpt-4o",
                                            messages = [{"role": "assistant", "content": gpt_prompt}, ], stream = True,
                                            max_tokens = 500)

    for chunk in stream:
        x.write(chunk.choices[0].delta.content or "")

    return x.getvalue()


def audio_data_extraction(file, prompt):
    extracted_data = file.extracted_data.filter(name = "extracted_text").first()
    if not extracted_data:
        text = speech_to_text(file.file)
        file.create_extracted_data(name = "extracted_text", data = text)
    else:
        text = extracted_data.data
    data = string_data_extraction(text, prompt)
    return data


def video_data_extraction(file, prompt):
    extracted_data = file.extracted_data.filter(name = "extracted_text").first()
    if not extracted_data:
        text = video_to_text(file.file)
        file.create_extracted_data(name = "extracted_text", data = text)
    else:
        text = extracted_data.data
    data = string_data_extraction(text, prompt)
    return data
