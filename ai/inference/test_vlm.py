import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText

MODEL_ID = "HuggingFaceTB/SmolVLM-256M-Instruct"

print("Loading processor...")
processor = AutoProcessor.from_pretrained(MODEL_ID)

print("Loading model...")
model = AutoModelForImageTextToText.from_pretrained(
    MODEL_ID,
    dtype=torch.float32,
)

model = model.to("cpu")

print("Model loaded successfully!")

image = Image.open("ai/datasets/test.jpg").convert("RGB")

print("\n===================================")
print("       SatQuery AI - VLM Test")
print("===================================")
print("Ask questions about the satellite image.")
print("Type 'exit' to quit.")

while True:

    question = input("\nYou: ")

    if question.lower().strip() == "exit":
        print("Exiting...")
        break

    if not question.strip():
        continue

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                },
                {
                    "type": "text",
                    "text": question,
                },
            ],
        }
    ]

    prompt = processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
    )

    inputs = processor(
        text=prompt,
        images=[image],
        return_tensors="pt",
    )

    inputs = {
        key: value.to("cpu")
        for key, value in inputs.items()
    }

    print("\nVLM is analyzing...")

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=100,
        )

    answer = processor.batch_decode(
        generated_ids,
        skip_special_tokens=True,
    )[0]

    # Remove the prompt portion from the output
    if "Assistant:" in answer:
        answer = answer.split("Assistant:", 1)[1].strip()

    print("\nSatQuery AI:", answer)
