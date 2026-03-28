import spacy

nlp = spacy.load("en_core_web_sm")

ENTITY_TYPES = {"PERSON", "ORG", "GPE", "DATE", "EVENT", "FAC", "LOC"}

def extract_entities(pages: list) -> list:
    mentions = []

    for page in pages:
        text = page.get("text", "").strip()
        if not text:
            continue

        doc = nlp(text[:10000])

        for ent in doc.ents:
            if ent.label_ not in ENTITY_TYPES:
                continue
            if len(ent.text.strip()) < 2:
                continue

            start = max(0, ent.start_char - 60)
            end = min(len(text), ent.end_char + 60)
            context = text[start:end].replace("\n", " ").strip()

            mentions.append({
                "name": ent.text.strip(),
                "type": ent.label_,
                "page_num": page["page_num"],
                "context": context
            })

    return mentions


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    from extractor import extract_document

    if len(sys.argv) < 3:
        print("Usage: python ner.py <file_path> <corpus>")
        sys.exit(1)

    doc = extract_document(sys.argv[1], sys.argv[2])
    mentions = extract_entities(doc["pages"])

    print(f"\nFound {len(mentions)} entity mentions\n")

    seen = set()
    for m in mentions:
        key = (m["name"], m["type"])
        if key not in seen:
            print(f"  [{m['type']}] {m['name']}")
            seen.add(key)