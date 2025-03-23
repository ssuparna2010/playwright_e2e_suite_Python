import pathlib
from typing import List, Dict, Any, Optional
from venv import logger
from azure.ai.evaluation import evaluate, QAEvaluator, SimilarityEvaluator, GroundednessEvaluator, MeteorScoreEvaluator, RelevanceEvaluator
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
import os
from dotenv import load_dotenv
# from deepeval.metrics import ExactMatchMetric
# from deepeval.test_case import LLMTestCase
from pathlib import Path
import json
from openai import AzureOpenAI
import pandas as pd
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
import string

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
nltk.download('punkt')
nltk.download('stopwords')

def get_azure_config():
    """Centralized function to fetch Azure AI project and judge model configurations."""
    azure_ai_project = {
        "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID"),
        "resource_group_name": os.getenv("AZURE_RESOURCE_GROUP"),
        "project_name": os.getenv("AZURE_PROJECT_NAME"),
    }
    
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")

    search_client = None
    # SearchClient(
    # endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    # index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
    # credential=credential
    #     )
   

    judge_model = {
        "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_key": token_provider(),  # Fetch the token as a string
        "azure_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION")
    }
    
    # Validate judge_model configuration
    if not all(judge_model.values()):
        raise ValueError("Missing required configuration in judge_model")
   
    return azure_ai_project, judge_model,search_client
def preprocess_text(text: str) -> str:
    """
    Preprocess the text by removing punctuation, stopwords, and converting to lowercase.
    """
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Convert to lowercase
    text = text.lower()
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    text = ' '.join([word for word in text.split() if word not in stop_words])
    return text

def calculate_cosine_similarity(actual_response_text: str,expected_text: str) -> float:
    """
    Calculate the cosine similarity between two texts.
    """
    print("\nsimilarity starts",actual_response_text,expected_text)
    # Preprocess the texts
    text1 = preprocess_text(actual_response_text)
    text2 = preprocess_text(expected_text)

    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text1, text2])

    # Calculate cosine similarity
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])

    print("\nsimilarity",similarity)
    return similarity[0][0]


def call_to_ai_application(query: str) -> str:
    """Calls the AI application with the given query and returns the response."""
    token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    if not deployment or not endpoint:
        raise ValueError("Environment variables AZURE_OPENAI_DEPLOYMENT and AZURE_OPENAI_ENDPOINT must be set")

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        # api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_ad_token_provider=token_provider,
    )

    completion = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "user",
                "content": query,
            }
        ],
        max_tokens=800,
        temperature=0.7,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=False,
    )

    message = completion.to_dict()["choices"][0]["message"]
    return message["content"]


def perform_evaluation(script_id,step_no, step_desc, evaluators, query, context, ground_truth, input_value):
    """Performs evaluation based on the specified evaluator."""
    evaluation_dir = pathlib.Path("./Evaluation_Output")
    evaluation_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists

    # Generate the output path using the input_value
    output_path_location = evaluation_dir / f"{script_id}.json"
    try:
        # Call AI application to get the response
        evaluators = evaluators.lower()
        # Determine which evaluation function to use
        if evaluators == "qa_evaluator":
            response = call_to_ai_application(query)
            print(f"Response: {response}")
            if (query) or (context) or (ground_truth):
                eval_output = evaluate_qa_response(output_path_location, query, response, context, ground_truth, evaluators,input_value)
            
            else:
                logger.error(f"Failed Step {script_id} - Evaluators: {evaluators}, Query: {query}, Context: {context}, Ground Truth: {ground_truth}")                
                step_isOK = 1
                actual_result = "No evaluators found"
                expected_result = "Evaluation should be performed"
    
        elif evaluators == "qa_evaluator_csv":
            eval_output = evaluate_qa_response_basedonCSV(output_path_location, evaluators, input_value)
        elif evaluators == "qa_evaluator_json":
            eval_output = run_qa_evaluate_response_basedonjson(output_path_location,evaluators,input_value)
        else:
            raise ValueError(f"Unsupported evaluator: {evaluators}")

        actual_result = "Evaluation performed"
        expected_result = "Evaluation should be performed"
        step_isOK = 0  # Assume success for evaluation steps
        # Append the evaluation output to a common file
        append_to_common_file(step_no, step_desc, evaluators, query, context, ground_truth, input_value, eval_output)
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        step_isOK = 1  # Mark step as failed
        actual_result = f"Error: {str(e)}"
        expected_result = "Evaluation should be performed"

    return step_isOK, actual_result, expected_result,output_path_location

def append_to_common_file(step_no, step_desc, evaluators, query, context, ground_truth, input_value, eval_output):
    common_file_path = Path("./consolidated_output.json")
    eval_result = {
        "step_no": step_no,
        "step_desc": step_desc,
        "evaluators": evaluators,
        "query": query,
        "context": context,
        "ground_truth": ground_truth,
        "input_value": input_value or None ,
        "eval_output": eval_output
    }

    # Read existing data from the common file
    if common_file_path.exists():
        with open(common_file_path, "r") as f:
            common_data = json.load(f)
    else:
        common_data = []

    # Append the new evaluation result
    common_data.append(eval_result)

    # Write the updated data back to the common file
    with open(common_file_path, "w") as f:
        json.dump(common_data, f, indent=4)

async def callback(
    messages: List[Dict],
    stream: bool = False,
    session_state: Any = None,  # noqa: ANN401
    context: Optional[Dict[str, Any]] = None,
) -> dict:
    messages_list = messages["messages"]
    # get last message
    latest_message = messages_list[-1]
    query = latest_message["content"]
    context = None
    # call your endpoint or ai application here
    response = call_to_ai_application(query)
    # we are formatting the response to follow the openAI chat protocol format
    formatted_response = {
        "content": response,
        "role": "assistant",
        "context": {
            "citations": None,
        },
    }
    messages["messages"].append(formatted_response)
    print(messages)
    return {"messages": messages["messages"], "stream": stream, "session_state": session_state, "context": context}

def evaluate_qa_response(
    output_path_location:str,
    query: str,
    response: str,
    context: Optional[str],
    ground_truth: str,
    evaluator_name: str,
    input_value: str
) -> Dict[str, Any]:
    """Evaluates the response using the QA Evaluator."""

    print("Evaluating response...", query, context, ground_truth)
    
    azure_ai_project, judge_model, SearchClient = get_azure_config()

    print(f"Output path: {output_path_location}")
    try:
        evaluatormodel = QAEvaluator(model_config=judge_model)
        print(f"Evaluator instance created: {evaluatormodel}")
    except Exception as e:
        print(f"Error creating evaluator instance: {str(e)}")
        raise
    
    # Ensure all values are strings
    eval_input_data = {
            "query": str(query),  # Ensure query is a string
            "response": str(response),  # Ensure response is a string
            "context": str(context) if context is not None else "",  # Ensure context is a string
            "ground_truth": str(ground_truth),  # Ensure ground_truth is a string
        }
    

    # Save the eval_input_data to a JSON file
    data_file_path = pathlib.Path("./custom_input_eval.jsonl")
    with open(data_file_path, "w") as f:
        json.dump(eval_input_data, f)

    # Log the contents of the JSON file for debugging
    with open(data_file_path, "r") as f:
        file_contents = f.read()
        print(f"Contents of {data_file_path}: {file_contents}")

    eval_output = evaluate(
        data=str(data_file_path),  # Pass the file path as a string
        evaluators={"QAEvaluator": evaluatormodel},
        evaluator_config={
            "QAEvaluator": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}",
                    "context": "${data.context}",
                    "ground_truth": "${data.ground_truth}",
                }
            }
        },
        azure_ai_project=azure_ai_project,
        output_path=output_path_location
    )
    print(f"Evaluation Output: {eval_output}")

    return eval_output

def evaluate_qa_response_basedonCSV(
    output_path_location:str,
    evaluator_name: str,
    input_values: str  
) -> Dict[str, Any]:
    """Evaluates the response using the QA Evaluator using CSV."""    
    
    azure_ai_project, judge_model, SearchClient = get_azure_config()
    evaluator = QAEvaluator(model_config=judge_model)

     # Load the input data from the CSV file
    df = pd.read_csv(input_values, dtype=str, usecols=["Questions", "Expected Answers"])
    df = df.rename(columns={"Questions": "query", "Expected Answers": "ground_truth", "Reference": "context"})
    print("response--", df["query"])

    azure_ai_project, judge_model,search_client = get_azure_config()
   
   
  
        # Save the eval_input_data to a JSON file
    data_file_path = pathlib.Path("./custom_input_eval.jsonl")
    with open(data_file_path, "w") as f:
        json.dump("test", f)

    # Log the contents of the JSON file for debugging
    with open(data_file_path, "r") as f:
        file_contents = f.read()
        print(f"Contents of {data_file_path}: {file_contents}")
    eval_output = evaluate(
        data=str(data_file_path),  # Pass the file path as a string
        evaluators={evaluator_name: evaluator},
        evaluator_config={
            evaluator_name: {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}",
                    "context": "${data.context}",
                    "ground_truth": "${data.ground_truth}",
                }
            }
        },
        azure_ai_project=azure_ai_project,
        output_path=output_path_location
    )
    print(f"Evaluation Output: {eval_output}")

    return eval_output

def run_qa_evaluate_response_basedonjson(output_path_location,evaluator_name: str,input_values):
    
    azure_ai_project, judge_model, SearchClient = get_azure_config()
   
    try:
        evaluatormodel = QAEvaluator(model_config=judge_model)
        print(f"Evaluator instance created: {evaluatormodel}")
    except Exception as e:
        print(f"Error creating evaluator instance: {str(e)}")
        raise
        

    # Save the eval_input_data to a JSON file
    data_file_path = pathlib.Path(input_values)

    eval_output = evaluate(
        data=str(data_file_path),  # Pass the file path as a string
        evaluators={"QAEvaluator": evaluatormodel},
        evaluator_config={
            "QAEvaluator": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}",
                    "context": "${data.context}",
                    "ground_truth": "${data.ground_truth}",
                }
            }
        },
        azure_ai_project=azure_ai_project,
        output_path=output_path_location
    )
    print(f"Evaluation Output: {eval_output}")

    return eval_output

