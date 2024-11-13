import requests
import argparse
import json
import prompty
from dataclasses import dataclass, asdict
from typing import List
import prompty.azure
from prompty.tracer import trace, Tracer, console_tracer, PromptyTracer
from halo import Halo


# Uncomment if you want enable tracing and feedback in the console
#Tracer.add("console", console_tracer)
json_tracer = PromptyTracer()
Tracer.add(PromptyTracer, json_tracer.tracer)


@dataclass
class Metadata:
    width: int
    height: int

@dataclass
class BoundingBox:
    x: int
    y: int
    w: int
    h: int

@dataclass
class Value:
    text: str
    confidence: float
    boundingBox: BoundingBox

@dataclass
class DenseCaptionResult:
    values: List[Value]

@dataclass
class AnalyzeResult:
    modelVersion: str
    metadata: Metadata
    denseCaptionsResult: DenseCaptionResult

@dataclass
class AnalyzeRequest:
    uri: str

# In Azure OpenAI Service the Cognitive Service Endpoint are listed under "Computer vision"
CognitiveServicesEndpoint = "YourCognitiveServiceEndPoint"
CognitiveServiceEndpointKey = "CognitiveServiceEndPointKey" 
DefaultImageURL = "Default URL to an image that you want to analyze"

class DenseCaption:
    def generate_dense_caption(self, image_url: str):
        endpoint = CognitiveServicesEndpoint
        url = f"{endpoint}computervision/imageanalysis:analyze?features=denseCaptions&gender-neutral-caption=false&api-version=2023-10-01"
        key = CognitiveServiceEndpointKey 

        headers = {
            'Ocp-Apim-Subscription-Key': key,
            'Content-Type': 'application/json; charset=utf-8'
        }

        analyze_request = AnalyzeRequest(uri=image_url)
        json_data = asdict(analyze_request)

        response = requests.post(url, headers=headers, json=json_data)
        response_content = response.text

        data = json.loads(response_content)
        try:
            deserialized_object = self.from_dict(AnalyzeResult, data)
            captions = [value.text for value in deserialized_object.denseCaptionsResult.values]
            return captions
        except KeyError as e:
            print(f"KeyError: {e}. Please check the JSON response structure.")
            return []

    def from_dict(self, data_class, data):
        if isinstance(data, list):
            return [self.from_dict(data_class.__args__[0], item) for item in data]
        if isinstance(data, dict):
            fieldtypes = {f.name: f.type for f in data_class.__dataclass_fields__.values()}
            return data_class(**{k: self.from_dict(fieldtypes[k], v) for k, v in data.items()})
        return data

class SceneDescriptionAssistant:
    def __init__(self, api_key, endpoint):
        self.api_key = api_key
        self.endpoint = endpoint

    @trace
    def run(
        question: any
    ) -> str:
        result = prompty.execute(
            "imagecaption.prompty",
            inputs={"question": question}
        )
        return result
    
# Usage example
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate dense captions for an image.")
    parser.add_argument(
        "image_url",
        type=str,
        nargs='?',
        default=DefaultImageURL,
        help="The URL of the image to analyze."
    )
    args = parser.parse_args()
    print("Processing image:", args.image_url)
    spinner = Halo(
        text='Generating dense captions...', 
        spinner= {
            'interval': 100,
            'frames': [
            "⣾",
			"⣽",
			"⣻",
			"⢿",
			"⡿",
			"⣟",
			"⣯",
			"⣷"]
        }
    )
    spinner.start()
    denseCaption = DenseCaption()
    captions = denseCaption.generate_dense_caption(args.image_url)
    spinner.stop()

      
    if captions:
        spinner = Halo(
            text='Processing scene description...', 
            spinner={
        'interval': 100,
        'frames': [
            "⣾",
			"⣽",
			"⣻",
			"⢿",
			"⡿",
			"⣟",
			"⣯",
			"⣷"]
        }
        )
        spinner.start()
        results = SceneDescriptionAssistant.run(captions)
        if results:
            print("\n")
            print("Scene Description:", results)
        spinner.stop()
