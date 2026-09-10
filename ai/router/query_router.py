from typing import Optional, Dict

# ============================================================
# SATQUERY SMART QUERY ROUTER
# ============================================================

# Classes that YOLO understands
YOLO_CLASS_MAP = {
    "building": ["Building", "buildings", "house", "houses"],
    "car": ["car", "cars", "vehicle", "vehicles", "small car", "passenger car"],
    "truck": ["truck", "trucks", "cargo truck", "lorry"],
    "bus": ["bus", "buses"],
    "excavator": ["excavator", "bulldozer"],
}


def classify_query(query: str) -> Dict:
    """
    Decide which AI pipeline should answer the question.

    Returns:
        {
            "route": "detection" | "vlm" | "segmentation",
            "requested_class": "car" | "building" | None,
            "show_all": bool
        }
    """

    q = query.lower().strip()

    # --------------------------------------------------------
    # SEGMENTATION
    # --------------------------------------------------------

    segmentation_keywords = [
        "segment",
        "segmentation",
        "outline",
        "mask",
        "boundary",
        "boundaries",
    ]

    if any(word in q for word in segmentation_keywords):
        return {
            "route": "segmentation",
            "requested_class": None,
            "show_all": False,
        }

    # --------------------------------------------------------
    # DETECT ALL OBJECTS
    # --------------------------------------------------------

    detect_all_keywords = [
        "detect all",
        "all objects",
        "everything",
        "all visible objects",
        "detect objects",
        "find all objects",
    ]

    if any(word in q for word in detect_all_keywords):
        return {
            "route": "detection",
            "requested_class": None,
            "show_all": True,
        }

    # --------------------------------------------------------
    # SPECIFIC YOLO OBJECT
    # --------------------------------------------------------

    detection_words = [
        "detect",
        "count",
        "how many",
        "find",
        "identify",
        "locate",
        "visible",
    ]

    if any(word in q for word in detection_words):

        for object_name, keywords in YOLO_CLASS_MAP.items():
            if any(keyword in q for keyword in keywords):
                return {
                    "route": "detection",
                    "requested_class": object_name,
                    "show_all": False,
                }

    # --------------------------------------------------------
    # DEFAULT TO GEMINI / VLM
    # --------------------------------------------------------

    return {
        "route": "vlm",
        "requested_class": None,
        "show_all": False,
    }


if __name__ == "__main__":

    while True:
        query = input("\nQuery: ")

        if query.lower() == "exit":
            break

        print(classify_query(query))