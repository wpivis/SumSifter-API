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
    documentId: Optional[str] = None
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


class GenerateEmailRequestModel(BaseModel):
    conversationId: str
    documentId: str
    promptType: Literal["general", "source", "email"]
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

SYSTEM_PROMPT_EMAIL = """
You will be provided with an article and a prompt for generating an email.
Read the article and create email content based on the prompt.

The email should be structured as follows:

2. **Greeting**: Hi, I am reading this report and came across the section below.
3. **1-Sentence Description**: A 1 sentence summary of the document to give context about the report and snippet.
4. **Text of Interest**: The prompt text (include the request prompt here that was appended).
5. **Bullet Points**: Each bullet point in the email body that is derived from the prompt. Focus its relavance to the document. 


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
            return jsonify(
                {
                    "conversationId": req.conversationId
                    if req.conversationId
                    else str(uuid.uuid4()),
                    "summary": fake_response["summary"],
                    "source": fake_response["source"],
                }
            )

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
                # "sentence_sequence": document.sentence_sequence,
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
        model="gpt-4o-mini", messages=conversation["messages"]
    )

    # update conversation list
    response_text = response["choices"][0]["message"]["content"].strip()

    formatted_response = json.loads(response_text)
    # add index to formatted_response
    for i, block in enumerate(formatted_response["summary"]):
        block["id"] = str(i + 1)

    conversation["messages"].append({"role": "assistant", "content": response_text})

    # source = conversation["document"]["sentence_sequence"]
    source = conversation["document"]["markdown"]

    cache.set(conversationId, conversation, timeout=3600)

    return jsonify(
        {
            "conversationId": conversationId,
            "summary": formatted_response["summary"],
            "source": source,
        }
    )


SYSTEM_PROMPT_GLOBAL_SUMMARY = """
You will be provided with multiple articles.

You will be prompted to provide a single summary of the articles.
The sentences in the summary must be attributed to id of the article.

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


@bp.route("/generate-multiple/", methods=["POST"])
def generate_multiple():
    try:
        req = GenerateSummaryMultipleDocsRequestModel.model_validate(request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 400
    
    if Config.FAKE_RESPONSE:
        print("responding with fake response")
        with open("./fake_response/global_summary.json", "r") as f:
            fake_response = json.load(f)
            return jsonify(fake_response)


    document_summary_source = []
    if req.conversationId is None:
        # New conversation
        conversationId = str(uuid.uuid4())

        # get documents
        # pregenerated_summaries_response = []
        global_markdown_content = []

        idx = 0
        # Create separate conversations for each docs
        # Add pre-generated responses to the conversations
        for doc_id in req.documentIds:
            print(doc_id)
            # markdown_content = {}

            idx += 1
            with open(f"pregenerated_summaries/{doc_id}") as f:
                docConversationId = str(uuid.uuid4())
                r = json.load(f)

                # for line in r["source"]:
                #     markdown_content[line["id"]] = line["text"] if line["text"] != "\n" else ""
                markdown_content = [
                    {"id": i["id"], "text": i["text"]} for i in r["source"]
                ]

                global_markdown_content.append(
                    {
                        "id": idx,
                        "text": ["\n".join([i["text"] for i in r["summary"]])],
                    }
                )

                # pregenerated_summaries_response.append({
                #     "conversationId": docConversationId,
                #     "summary": r["summary"],
                #     "source": r["source"],
                # })

                conversation = {
                    "document": {
                        "id": doc_id,
                        # "markdown": markdown_content,
                        "markdown": markdown_content,
                    },
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        # {"role": "user", "content": f"Original Article:\n\n{markdown_content}"},
                        {
                            "role": "user",
                            "content": f"Original Article:\n\n{markdown_content}",
                        },
                        {
                            "role": "assistant",
                            "content": json.dumps({"summary": r["summary"]}),
                        },
                    ],
                }

                document_summary_source.append(
                    {
                        "conversationId": docConversationId,
                        "summary": r["summary"],
                        "source": r["source"],
                    }
                )

                print(docConversationId)
                cache.set(docConversationId, conversation, timeout=3600)

        conversation = {
            "document": {
                "ids": req.documentIds,
                "docConversationIds": [
                    i["conversationId"] for i in document_summary_source
                ],
                # "markdown": markdown_content,  # Include markdown content
            },
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_GLOBAL_SUMMARY},
                {
                    "role": "user",
                    "content": f"Original Articles :\n\n{global_markdown_content}",  # Use markdown content
                },
            ],
        }

    else:
        conversationId = req.conversationId
        conversation = cache.get(conversationId)

        # Reset and update the conversation with updated summaries
        global_markdown_content = []

        for docId in conversation["document"]["docConversationIds"]:
            # Get the conversation
            docConversation = cache.get(docId)
            # Get the updated summary
            updated_summary = docConversation["messages"][-1]["content"]
            # Add the updated summary to the global summary
            global_markdown_content.append(updated_summary)

        # Add the global summary to the conversation
        conversation["messages"] = [
            {"role": "system", "content": SYSTEM_PROMPT_GLOBAL_SUMMARY},
            {
                "role": "user",
                "content": f"Original Articles :\n\n{global_markdown_content}",  # Use markdown content
            },
        ]

    # Generate a global summary
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
        model="gpt-4o-mini", messages=conversation["messages"]
    )

    # update conversation list
    response_text = response["choices"][0]["message"]["content"].strip()

    formatted_response = json.loads(response_text)
    # add index to formatted_response
    for i, block in enumerate(formatted_response["summary"]):
        block["id"] = str(i + 1)

    conversation["messages"].append({"role": "assistant", "content": response_text})

    cache.set(conversationId, conversation, timeout=3600)

    return jsonify(
        {
            "conversationId": conversationId,
            "summary": formatted_response["summary"],
            "individualDocuments": document_summary_source,
        }
    )

@bp.route("/generate-email/", methods=["POST"])
def generate_email():
    try:
        req = GenerateEmailRequestModel.model_validate(request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 400

    # Now conversationId is always provided
    conversationId = req.conversationId

    # Get existing conversation from cache
    conversation = cache.get(conversationId)

    if conversation is None:
        return jsonify({"error": "Invalid conversationId"}), 400

    messages = [{"role": "system", "content": SYSTEM_PROMPT_EMAIL}]

    if req.promptType == "source":
        prompt = f"Update the email content with response specific to the following sentence from the original article: {req.sourceTargetText}\n\n----------\n{req.prompt}"
    elif req.promptType == "summary":
        prompt = f"Update the email content with response specific to the following sentence from the previous summary: {req.summaryTargetText}\n\n----------\n{req.prompt}"
    else:
        prompt = f"{req.prompt}"

    messages.append({"role": "user", "content": prompt})

    # call API
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini", messages=messages
    )

    # update conversation list
    response_text = response["choices"][0]["message"]["content"].strip()

    return jsonify(
        {
            "conversationId": conversationId,
            "emailContent": response_text,  # Return the response text as string
        }
    )
