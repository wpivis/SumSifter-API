from typing_extensions import Literal
from typing import Optional
from app.summaries import bp
from pydantic import BaseModel, ValidationError
from flask import request, jsonify
import openai
from dotenv import load_dotenv
import os
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


@bp.route("/")
def index():
    return "summaries : /"


SYSTEM_PROMPT = """
You will be provided with an article in markdown format with each sentence that ends with a sentence ID in the form of "(S1)", "(S2)", and so on. Ensure that you read the article carefully before providing a summary.

You will be prompted to provide a summary of the article.
The summary must be a list of sentences that are present in the article.
Each sentence in the summary must be attributed to sentences in the original article by citing the sentence IDs.
Maintain the markdown format.

Use the following json format to answer.
{
    "summary": [
        {"text": "Sentence 1", "sources": ["S1", "S2"]},
        {"text": "Sentence 2", "sources": ["S3", "S4"]},
        {"text": "Sentence 3", "sources": ["S5", "S6"]},
        {"text": "Sentence 4", "sources": ["S7", "S8"]},
        {"text": "Sentence 5", "sources": ["S9", "S10"]}
    ]
}

Do not include any text outside of the JSON format.
"""


@bp.route("/generate/", methods=["POST"])
def categories():
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
        document.read()

        # Convert document to markdown and save
        markdown_content = document.convert_to_markdown()
        document.save_markdown(f"documents/{req.documentId}.md")

        # Parse the markdown content to generate the source list
        source_list = document.parse_markdown()

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
        prompt = f"Provide response specific to the following sentence from the original article: {req.sourceTargetText}\n\n----------\n{req.prompt}"
    else:
        prompt = req.prompt

    # add new prompt to conversation list
    conversation["messages"].append({"role": "user", "content": prompt})

    # call API
    response = openai.ChatCompletion.create(
        model="gpt-4", messages=conversation["messages"]
    )

    # update conversation list
    response_text = response["choices"][0]["message"]["content"].strip()

    formatted_response = json.loads(response_text)
    conversation["messages"].append({"role": "assistant", "content": response_text})

    source = conversation["document"]["sentence_sequence"]

    cache.set(conversationId, conversation, timeout=3600)

    return jsonify(
        {
            "conversationId": conversationId,
            "summary": formatted_response["summary"],
            "source": source_list,  # Use the parsed markdown content for the source list
        }
    )
