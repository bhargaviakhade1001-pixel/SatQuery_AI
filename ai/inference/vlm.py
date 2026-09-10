import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText


class VLM:

    MODEL_ID = "HuggingFaceTB/SmolVLM-256M-Instruct"

    def __init__(self):
        print("Loading VLM processor...")

        self.processor = AutoProcessor.from_pretrained(
            self.MODEL_ID
        )

        print("Loading VLM model...")

        self.model = AutoModelForImageTextToText.from_pretrained(
            self.MODEL_ID,
            dtype=torch.float32,
        )

        self.model = self.model.to("cpu")

        print("VLM loaded successfully!")

    def ask(self, image_path, question):

        image = Image.open(image_path).convert("RGB")

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                    },
                    {
                        "type": "text",
                        "text": f"""
You are SatQuery AI, a remote-sensing image analysis assistant.

Analyze only what is visibly present in the satellite image.

Focus on:
- buildings and structures
- roads and transportation
- vegetation
- water bodies
- land cover and land use
- urban or rural characteristics
- other clearly visible geographic features

Do not invent objects, locations, measurements, or details.
If something cannot be determined from the image, say so.

Answer the user's question directly and concisely.

User question:
{question}
""",
                    },
                ],
            }
        ]

        prompt = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
        )

        inputs = self.processor(
            text=prompt,
            images=[image],
            return_tensors="pt",
        )

        inputs = {
            key: value.to("cpu")
            for key, value in inputs.items()
        }

        with torch.no_grad():

            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=60,
            )

        answer = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )[0].strip()

        if "Assistant:" in answer:
            answer = answer.split(
                "Assistant:", 1
            )[1].strip()

        return answer
