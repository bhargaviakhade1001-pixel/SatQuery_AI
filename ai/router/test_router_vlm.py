from ai.router.query_router import classify_query
from ai.inference.vlm import VLM


IMAGE_PATH = "ai/datasets/test.jpg"


print("Loading VLM...")
vlm = VLM()

print("\n===================================")
print("       SatQuery AI")
print("===================================")
print("Type 'exit' to quit.")


while True:

    query = input("\nYou: ")

    if query.lower().strip() == "exit":
        break

    task = classify_query(query)

    print(f"Route: {task}")

    if task == "vlm":

        answer = vlm.ask(
            IMAGE_PATH,
            query
        )

        print("\nSatQuery AI:", answer)

    elif task == "detection":

        print("\nDetection module not connected yet.")

    elif task == "segmentation":

        print("\nSegmentation module not connected yet.")
