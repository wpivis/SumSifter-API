from typing_extensions import Literal
from typing import Optional, List
from app.summaries import bp
from pydantic import BaseModel, ValidationError
from flask import request, jsonify
import openai
import uuid
import json

from config import Config
from .document_reader import DocumentReader

from app import cache

openai.api_key = Config.OPENAI_API_KEY

class GenerateSummaryRequestModel(BaseModel):
    conversationId: Optional[str] = None
    documentId: str
    promptType: Literal["general", "source", "summary"]
    sourceTargetText: Optional[str] = None
    summaryTargetText: Optional[str] = None
    prompt: str

class GenerateSummaryMultipleDocsRequestModel(BaseModel):
    conversationId: Optional[str] = None
    documentIds: List[str]
    promptType: Literal["general", "source", "summary"]
    sourceTargetText: Optional[str] = None
    summaryTargetText: Optional[str] = None
    prompt: str

@bp.route("/")
def index():
    return "summaries : /"


SYSTEM_PROMPT = """
You will be provided with an article in a json format with texts in markdown.
The texts are broken down into blocks and are assigned an id.

You will be prompted to provide a summary of the article.
The sentences in the summary must be attributed to id(s) of the block in the
original article.

You can use markdown within the summary.

Use the following json format to answer.
{
	"summary": [
    	{"text": "Block 1", "sources": ["1", "2"]},
    	{"text": "Block 2", "sources": ["3", "4"]},
    	{"text": "Block 3", "sources": ["5", "6"]},
    	{"text": "Block 4", "sources": ["7", "8"]},
    	{"text": "Block 5", "sources": ["9", "10"]}
	]
}

Do not include any text outside of the JSON format.
"""


@bp.route("/generate/", methods=["POST"])
def generate():
    try:
        req = GenerateSummaryRequestModel.model_validate(request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 400

    if Config.FAKE_RESPONSE:
        print("responding with fake response")
        with open("./fake_response/summary.json", "r") as f:
            fake_response = json.load(f)
            return jsonify({
                "conversationId": req.conversationId if req.conversationId else str(uuid.uuid4()),
                "summary": fake_response["summary"],
                "source": fake_response["source"],
            })

    if req.conversationId is None:
        # New conversation
        conversationId = str(uuid.uuid4())

        # get document
        document = DocumentReader(f"documents/{req.documentId}")

        # Convert document to markdown 
        markdown_content = document.convert_to_markdown()
        
        conversation = {
            "document": {
                "id": req.documentId,
                "sentences": document.sentences,
                "sentence_sequence": document.sentence_sequence,
                "markdown": markdown_content,  # Include markdown content
            },
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Original Article:\n\n{markdown_content}",  # Use markdown content
                },
            ],
        }

    else:
        # Get existing conversation from cache
        conversationId = req.conversationId
        conversation = cache.get(conversationId)

    if req.promptType == "source":
        prompt = f"Update the summary with response specific to the following sentence from the original article: {req.sourceTargetText}\n\n----------\n{req.prompt}"
    elif req.promptType == "summary":
        prompt = f"Update the summary with response specific to the following sentence from the previous summary: {req.summaryTargetText}\n\n----------\n{req.prompt}"
    else:
        prompt = f"{req.prompt}"

    # add new prompt to conversation list
    conversation["messages"].append({"role": "user", "content": prompt})

    # call API
    response = openai.ChatCompletion.create(
        model="gpt-4", messages=conversation["messages"]
    )

    # update conversation list
    response_text = response["choices"][0]["message"]["content"].strip()

    formatted_response = json.loads(response_text)
    # add index to formatted_response
    for i, block in enumerate(formatted_response["summary"]):
        block["id"] = str(i + 1)


    conversation["messages"].append({"role": "assistant", "content": response_text})

    source = conversation["document"]["sentence_sequence"]

    cache.set(conversationId, conversation, timeout=3600)

    return jsonify(
        {
            "conversationId": conversationId,
            "summary": formatted_response["summary"],
            "source": source,
        }
    )


@bp.route("/generate-multiple/", methods=["POST"])
def generate_multiple():
    # Create separate conversations for each docs

    # Add pre-generated responses to the conversations

    # Generate a global summary

    # Return
    return jsonify({"message": "generate multiple"})
