from ai.inference.vlm import VLM


model = VLM()

answer = model.ask(
    "ai/datasets/test.jpg",
    "Is this area urban or rural?"
)

print("\n===== ANSWER =====")
print(answer)
