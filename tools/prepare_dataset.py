import argparse
import json
import os
import random
import re
import unicodedata
from typing import Dict, List


def _clean_system_prompt(text: str) -> str:
    text = _normalize_unicode(text)
    # Remove bold/quote requirements while keeping intent
    text = re.sub(
        r"Always express your personality traits naturally in \*\*bold\*\*.*?\n",
        "Express your personality traits naturally in your responses\n",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(
        r"Only mention symptoms from the provided list, put them in quotes.*?\n",
        "Only mention symptoms from the provided list and keep language natural.\n",
        text,
        flags=re.IGNORECASE,
    )
    return text


def _strip_stagedirections(text: str) -> str:
    text = _normalize_unicode(text)
    # Remove bracketed meta like [END SCENE] or (stage ...), standalone italic/asterisk blocks
    # Remove lines that are entirely bracketed annotations
    lines = []
    for line in text.splitlines():
        l = line.strip()
        if not l:
            continue
        if re.fullmatch(r"\[.*?\]", l):
            continue
        if re.fullmatch(r"\*.*?\*", l):
            continue
        lines.append(line)
    text = "\n".join(lines)
    # Remove inline bracketed meta
    text = re.sub(r"\[.*?\]", "", text)
    return text.strip()


def _normalize_unicode(text: str) -> str:
    if not text:
        return text
    # Normalize and replace common problematic unicode
    t = unicodedata.normalize("NFKC", text)
    replacements = {
        "\u2018": "'",  # left single quote
        "\u2019": "'",  # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u00a0": " ",  # nbsp
        "\u200b": "",   # zero width space
        "\u2026": "...",# ellipsis
    }
    for k, v in replacements.items():
        t = t.replace(k, v)
    # Collapse excessive whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _normalize_symptoms(symptoms: List[str]) -> List[str]:
    cleaned: List[str] = []
    for s in symptoms or []:
        s = _normalize_unicode(s).strip()
        # Remove explanatory sentences, keep short phrases; split on commas and semicolons
        parts = re.split(r"[;,]", s)
        for p in parts:
            p = p.strip()
            if not p:
                continue
            # Drop very long fragments and obvious boilerplate/differentials
            if len(p) > 80:
                continue
            if any(x in p.lower() for x in [
                "conditions affecting", "kidney stones", "gallstones", "crohn",
                "ectopic pregnancy", "older people", "there are tendons",
                "often have no symptoms", "this type of abdominal pain",
            ]):
                continue
            # Fix concatenations like kidney stonesorgallstones
            p = re.sub(r"([a-z])org([a-z])", r"\1 or \2", p)
            # Keep concise, human-expressible phrases
            cleaned.append(p)
    # Deduplicate while preserving order
    seen = set()
    result = []
    for s in cleaned:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            result.append(s)
    return result[:20]


def prepare_dataset(input_path: str, out_dir: str, val_ratio: float = 0.05, seed: int = 42, preserve_formatting: bool = True, output_suffix: str = ""):
    os.makedirs(out_dir, exist_ok=True)
    with open(input_path, "r", encoding="utf-8") as f:
        conversations = json.load(f)

    # Shuffle conversation_ids for split
    random.seed(seed)
    ids = [c.get("conversation_id") for c in conversations]
    random.shuffle(ids)
    val_cut = max(1, int(len(ids) * val_ratio))
    val_ids = set(ids[:val_cut])

    suffix = output_suffix or ("_strict" if preserve_formatting else "")
    train_out = open(os.path.join(out_dir, f"sft_train{suffix}.jsonl"), "w", encoding="utf-8")
    val_out = open(os.path.join(out_dir, f"sft_val{suffix}.jsonl"), "w", encoding="utf-8")
    all_out = open(os.path.join(out_dir, f"sft_all{suffix}.jsonl"), "w", encoding="utf-8")

    def _route(cid: int):
        return val_out if cid in val_ids else train_out

    dropped = 0

    for conv in conversations:
        cid = conv.get("conversation_id")
        messages = conv.get("messages", [])
        metadata: Dict = conv.get("metadata", {})

        if not messages:
            dropped += 1
            continue

        # Clean system message
        if messages[0].get("role") == "system":
            sys_content = messages[0]["content"]
            messages[0]["content"] = _normalize_unicode(sys_content) if preserve_formatting else _clean_system_prompt(sys_content)

        # Clean assistant turns and keep Doctor prefix intact on user turns
        cleaned_msgs: List[Dict] = []
        for m in messages:
            role = m.get("role")
            content = _normalize_unicode((m.get("content") or "").strip())
            if role == "assistant":
                content = _strip_stagedirections(content)
                if not preserve_formatting:
                    # Remove heavy markdown left-overs
                    content = re.sub(r"\*\*", "", content)
                    # Remove unnecessary hard quotes around phrases
                    content = re.sub(r'"([^\"]+)"', r'\\1', content)
            elif role == "user":
                # Ensure it remains as Doctor: ...
                if not content.lower().startswith("doctor:"):
                    content = f"Doctor: {content}"
            cleaned_msgs.append({"role": role, "content": content})

        # Normalize symptoms metadata (optional, retained for later use)
        if "symptoms" in metadata:
            metadata["symptoms"] = _normalize_symptoms(metadata.get("symptoms") or [])

        sample = {"messages": cleaned_msgs, "metadata": metadata, "conversation_id": cid}
        json.dump(sample, _route(cid))
        _route(cid).write("\n")
        json.dump(sample, all_out)
        all_out.write("\n")

    train_out.close()
    val_out.close()
    all_out.close()

    print(f"Prepared dataset. Dropped {dropped} conversations. Output: {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare SFT dataset from cleaned_finetuning_dataset.json")
    parser.add_argument("--input", default=os.path.join(os.path.dirname(__file__), "..", "cleaned_finetuning_dataset.json"))
    parser.add_argument("--out_dir", default=os.path.join(os.path.dirname(__file__), "..", "datasets"))
    parser.add_argument("--val_ratio", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--preserve_formatting", action="store_true", help="Keep bold/quotes and original system rules")
    parser.add_argument("--output_suffix", default="", help="Suffix for output filenames (e.g., _strict)")
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    out_dir = os.path.abspath(args.out_dir)
    prepare_dataset(
        input_path,
        out_dir,
        args.val_ratio,
        args.seed,
        preserve_formatting=bool(args.preserve_formatting),
        output_suffix=args.output_suffix,
    )


