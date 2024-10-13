from flask import Flask, render_template, request, jsonify
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains.question_answering import load_qa_chain
from langchain_community.callbacks import get_openai_callback
from langchain_openai import AzureChatOpenAI
from opencc import OpenCC
from openai import OpenAI
from dotenv import load_dotenv
from pydub import AudioSegment
import tempfile
import io
import os
import whisper


load_dotenv()
client = OpenAI()
model = whisper.load_model("base")
os.environ["AZURE_OPENAI_ENDPOINT"] = os.getenv("AZURE_OPENAI_ENDPOINT")
os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")

embeddings = AzureOpenAIEmbeddings(
        model="text-embedding-ada-002",
        openai_api_version=os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION")
)
app = Flask(__name__)
vector_store = Chroma(
    collection_name = "fareastonHR",
    embedding_function = AzureOpenAIEmbeddings(
        model="text-embedding-ada-002",
        openai_api_version=os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION")
    ),
    persist_directory = "../db/fareastonHRupdate2"
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
        llm = AzureChatOpenAI(
            azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            api_version = os.getenv("AZURE_OPENAI_CHAT_API_VERSION"),
            temperature = 0.2
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
    if 'audio' not in request.files:
        return jsonify({'error': '沒有接收到音訊文件'}), 400

    audio_file = request.files['audio']
    
    if audio_file:
        audio_data = audio_file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_audio:
            temp_audio.write(audio_data)
            temp_audio_path = temp_audio.name

        try:
            audio = AudioSegment.from_file(temp_audio_path, format="webm")
            wav_path = temp_audio_path.replace('.webm', '.wav')
            audio.export(wav_path, format="wav")
            result = model.transcribe(wav_path, fp16=False)
            transcript = result["text"]
            cc = OpenCC('s2t')
            text = cc.convert(transcript)
            return jsonify({'message': '音檔已處理', 'transcript': text})
        except Exception as e:
            return jsonify({'error': f'處理音訊時發生錯誤: {str(e)}'}), 500
        finally:
            os.unlink(temp_audio_path)
            if os.path.exists(wav_path):
                os.unlink(wav_path)

    return jsonify({'error': '沒有接收到音訊文件'}), 400

if __name__ == '__main__':
    app.run(debug=True, port = 3308)  