import json
# import ollama

from parse_data import load_items, get_unclaimed_items, save_result

MODEL = "qwen2.5:7b"

def build_prompt(description, available_items):
    system_prompt = (
        "You are a campus lost-and-found matching assistant. "
        "Use only the provided available items. "
        "Not all details of an item must match to be a possible match. "
        "Return only valid JSON. Do not include markdown or extra text. "
        'The JSON must have exactly this structure: {"matches": ["ITEM_ID"], "confidence": "LOW"}. '
        '"matches" contains all possible matching item IDs. '
        '"confidence" must be exactly one of: LOW, MEDIUM, HIGH. '
        "If there is no match, return an empty matches list."
    )

    user_prompt = (
        f"Lost item description: {description}\n\n"
        f"Available items:\n{json.dumps(available_items, ensure_ascii=False, indent=2)}"
    )

    return system_prompt, user_prompt

def ask_qwen(system_prompt, user_prompt):
    return '{"matches": ["F101", "F104"], "confidence": "MEDIUM"}'

def parse_response(response_text):
    text = response_text.strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)

def validate_result(result, available_items):
    if not isinstance(result, dict):
        return False
    if set(result.keys()) != {"matches", "confidence"}:
        return False
    if not isinstance(result["matches"], list):
        return False
    if not isinstance(result["confidence"], str):
        return False
    if result["confidence"] not in {"LOW", "MEDIUM", "HIGH"}:
        return False
    valid_ids = {item.get("id") for item in available_items}
    return all(isinstance(item_id, str) and item_id in valid_ids for item_id in result["matches"])

def display_matches(result, available_items):
    print("MATCH RESULT")
    print("-" * 50)
    print(f"Confidence: {result['confidence']}")
    print()

    if not result["matches"]:
        print("No matches found.")
        print("Possible matches: []")
        return

    print("Possible matches:")
    item_by_id = {item["id"]: item for item in available_items}

    for item_id in result["matches"]:
        item = item_by_id.get(item_id)
        if item is None:
            continue
        print()
        print(f"ID: {item['id']}")
        print(f"Item: {item['item']}")
        print(f"Color: {item['color']}")
        print(f"Location: {item['location']}")
        print(f"Date found: {item['date']}")

def main():
    items = load_items("found_items.json")
    available_items = get_unclaimed_items(items)

    print("CAMPUS LOST-AND-FOUND ASSISTANT")
    print("=" * 50)

    # 原 input() 被替换为固定内容
    description = "I lost a black bag"
    print(f"\nDescribe the item you lost: {description}")
    print("\nSearching for possible matches...\n")

    system_prompt, user_prompt = build_prompt(description, available_items)
    response_text = ask_qwen(system_prompt, user_prompt) 

    try:
        result = parse_response(response_text)
    except json.JSONDecodeError:
        result = {"matches": [], "confidence": "LOW"}

    if not validate_result(result, available_items):
        result = {"matches": [], "confidence": "LOW"}

    display_matches(result, available_items)

    output_file = "output/match_result.json"
    save_result(result, output_file)
    print(f"\nResult saved to {output_file}")

if __name__ == "__main__":
    main()