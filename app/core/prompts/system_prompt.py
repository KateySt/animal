SUMMARY_PROMPT = """
You are summarizing a conversation from the Animal Shelter platform.

If the input contains a <previous_summary> block, extend it with the facts from <new_messages> and return a single merged summary — do not repeat the previous summary verbatim, integrate it. If there is no previous summary, summarize the messages as given.

Produce a compact summary (max 200 words) that preserves:
- The main topics discussed
- Key data mentioned (animal names, invoice amounts, dates, statuses)
- Any unresolved questions or pending actions

Output plain prose, no headers. Be dense — every sentence must carry information.
""".strip()

TITLE_PROMPT = """
Generate a short chat title (max 6 words) based on this first user message.
Return only the title, no punctuation at the end, no quotes.
""".strip()

ASSISTANT_PREVIOUS_SUMMARY_TEMPLATE = """
<previous_summary>{previous_summary}</previous_summary>\n\n<new_messages>{new_transcript}</new_messages>
""".strip()
