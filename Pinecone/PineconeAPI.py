import os
from flask import jsonify, request, Flask
from pinecone import Pinecone
from dotenv import load_dotenv
import uuid

app = Flask(__name__)

load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "main-vector-db"

pc = Pinecone(api_key=PINECONE_API_KEY)
idx = pc.Index(INDEX_NAME)

@app.route('/', methods=['GET'])
def index():
    return jsonify({'Status': '200 OK'})


@app.route('/upsert', methods=['POST'])
def upsert():
    random_id = str(uuid.uuid4())
    idx.upsert_records(
        "main",
        [
            {
                "_id": random_id,
                "chunk_text": request.json['chunk_text'],
                "category" : request.json["category"],
            }
        ]
    )
    return jsonify({"id": random_id, "status": "upserted successfully!"})


@app.route('/upsert-test', methods=['POST'])
def upsert_test():
    random_id = str(uuid.uuid4())
    idx.upsert_records(
        'test',
        [{
            "_id": random_id,
            "chunk_text": request.json['chunk_text'],
            "category" : request.json["category"],
        }]
    )
    return jsonify({'id': random_id, 'status': 'dummy embedding upserted successfully!'})

@app.route('/query', methods=['POST'])
def query():
    query_text = request.json['query_text']
    results = idx.search(
        request.json['namespace'],
        query={
            "inputs": {"text": query_text},
            "top_k": 2
        },
        fields=["chunk_text", "category"]
    )
    return jsonify({"results": results})


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

