from flask import Flask, render_template, request, jsonify
import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains.question_answering import load_qa_chain
from langchain_community.callbacks import get_openai_callback
from langchain_openai import ChatOpenAI
from opencc import OpenCC

import openai
import io
import sys
from openai import OpenAI
client = OpenAI()


openai.api_key = os.getenv('OPENAI_API_KEY')
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

app = Flask(__name__)
vector_store = Chroma(
    collection_name="fareastonHRupdate",
    embedding_function=OpenAIEmbeddings(),
    persist_directory="../db/fareastonHPupdate2"
)

class NamedBytesIO(io.BytesIO):
    name = 'transcript.wav'

chat_history = []
data_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

if not os.path.exists(data_folder):
    os.makedirs(data_folder)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.form.get('user_input')
    db = None
    if not user_input:
        return jsonify({'error': 'No user input provided'})
    if user_input:
        docs = vector_store.similarity_search(user_input)
        print(docs)
        llm = ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.5
        )

        chain = load_qa_chain(llm, chain_type="stuff")

        with get_openai_callback() as cb:
            response = chain.invoke({"input_documents": docs,"question":user_input}, return_only_outputs=True)
        cc = OpenCC('s2t')
        answer=cc.convert(response['output_text'])
        chat_history.append({'user': user_input, 'assistant': response['output_text']})
        return jsonify({'response': answer})

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    audio_file = request.files['audio']
    if audio_file:
        audio_stream = NamedBytesIO(audio_file.read())
        audio_stream.name = 'transcript.wav' 

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_stream,
            response_format='text'
        )
        cc = OpenCC('s2t')
        text = cc.convert(transcript)
        return jsonify({'message': '音頻已處理', 'transcript': text})
    return jsonify({'error': '沒有接收到音訊文件'}), 400


if __name__ == '__main__':
    app.run(debug=True, port = 3308)  