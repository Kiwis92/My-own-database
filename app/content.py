"""
Inlezen en renderen van redactionele markdown-documenten uit content/.

Front matter (YAML-achtig blok tussen --- regels) wordt van de body
gescheiden en als metadata teruggegeven; de body wordt naar HTML gerenderd.
De bronbestanden in content/ blijven ongewijzigd — parsing gebeurt in-memory.
"""
import os
import markdown as md

CONTENT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content")


def _parse_front_matter(text: str):
    """Splits een optioneel '--- ... ---' front-matterblok van de body.

    Retourneert (meta: dict, body: str). Waarden worden ontdaan van
    omringende aanhalingstekens; geen externe YAML-afhankelijkheid nodig.
    """
    meta = {}
    body = text
    if text.startswith("---"):
        lines = text.splitlines()
        end = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i
                break
        if end is not None:
            for line in lines[1:end]:
                if ":" in line:
                    key, _, value = line.partition(":")
                    meta[key.strip()] = value.strip().strip('"').strip("'")
            body = "\n".join(lines[end + 1:]).lstrip("\n")
    return meta, body


def load_document(relative_path: str):
    """Lees een markdown-document uit content/ en render het.

    Retourneert een dict met 'meta', 'html' en 'title', of None als het
    bestand niet bestaat of buiten content/ zou vallen.
    """
    full = os.path.normpath(os.path.join(CONTENT_DIR, relative_path))
    if not full.startswith(CONTENT_DIR) or not os.path.isfile(full):
        return None

    with open(full, encoding="utf-8") as f:
        raw = f.read()

    meta, body = _parse_front_matter(raw)
    # HTML-commentaar (<!-- ... -->) in de bron blijft commentaar in de
    # gerenderde HTML en is dus niet zichtbaar op de pagina.
    html = md.markdown(body, extensions=["extra", "toc", "sane_lists"])
    return {
        "meta": meta,
        "html": html,
        "title": meta.get("titel") or meta.get("title") or "Juridisch",
    }
