#!/usr/bin/env python3

if __name__ == '__main__':
    import sys
    import os

    try:
        import elaphure
    except ImportError:
        ROOT=os.path.dirname(os.path.abspath(__file__))
        sys.path.append(os.path.dirname(ROOT)+"/elaphure")

    import elaphure.__main__

import os

def author(filename, meta):
    slug = filename[8:-3]
    return {
        "type": "author",
        "slug": slug,
        "name": meta.get("name", [slug])[0],
        "emails": meta.get("email", [])}

def wiki(filename, meta):
    slug = filename[5:-3]
    return {
        "type": "wiki",
        "slug": slug,
        "title": meta.get("title", [slug])[0],
        "authors": meta.get("author", []),
        "tags": meta.get("tag", [])}

def source_link(collection, pid):
    if collection == 'LUOGU':
        return f"https://www.luogu.org/problem/{pid}"

def prob(filename, meta):
    collection = os.path.dirname(filename[6:])
    pid = os.path.splitext(os.path.basename(filename))[0]
    slug = f"{collection}-{pid}"
    tags = meta.get("tag", [])
    if collection not in tags:
        tags = tags + [collection]

    result = {
        "type": "wiki",
        "slug": slug,
        "title": slug + ": " + meta.get("title", [""])[0],
        "authors": meta.get("author", []),
        "tags": tags,
        "collection": collection,
        "pid": pid,
        "canonical": meta.get("canonical", [None])[0]}
    source = source_link(collection, pid)
    if source is not None:
        result["source"] = source
    return result

def css(filename, meta):
    return {
        'type': 'css',
        'slug': filename[7:-4],
    }


SOURCE_FILES = [
    ("authors/*.md", 'markdown', author),
    ("wiki/**/*.md", 'markdown', wiki),
    ("probs/**/*.md", 'markdown', prob),
    ("static/*.css", 'wheezy', css)
]

URLS = [
    Rule(
        '/',
        defaults={'type': 'wiki', 'slug': 'index'},
        endpoint='wiki'),
    Rule(
        '/authors/',
        defaults={'type': 'author'},
        endpoint='author_list'),
    Rule(
        '/authors/<slug>.html',
        defaults={'type': 'author'},
        endpoint='author'),
    Rule(
        '/tagged/<path:slug>.html',
        defaults={'type': 'wiki'},
        endpoint='tagged'),
    Rule(
        '/<path:slug>.html',
        defaults={'type': 'wiki'},
        endpoint='wiki'),
    Rule(
        '/static/<slug>.css',
        defaults={'type': 'css'},
        endpoint='css'),
    Rule(
        '/<path:path>',
        endpoint='media')
]

class views(config):
    wiki = EntryView(template_name='templates/wiki.html')
    author_list = EntryListView(template_name='templates/authors.html')
    author = EntryView(template_name='templates/author.html')
    tagged = EntryView(template_name='templates/tagged.html')
    css = RawEntryView(mimetype='text/css')
    media = StaticFileView('wiki', ("*~", ".*", "*.md"))


def build_link(target, text=None):
    if target.startswith("@"):
        type = 'author'
        slug = target[1:]
    else:
        type = 'wiki'
        slug = target
    url = urls.build(type, {'slug': slug})

    _, values = urls.match(url)

    entries = db.select('''
SELECT source.*
FROM source
WHERE json_extract(source.metadata, '$.type') = {}
AND json_extract(source.metadata, '$.slug') = {}
''', type, slug)
    entry = None

    if not entries:
        warn(f"{type} {slug!r} not found")
    else:
        entry = entries[0]

    if text is None:
        if entry is None:
            text = target
        else:
            if values['type'] == 'author':
                text = entry["name"]
            else:
                text = entry["title"]

    if entry is not None and entry.get("canonical", None) is not None:
        return build_link(entry["canonical"], text)

    return url, text

from markdown.extensions import Extension
from markdown.inlinepatterns import Pattern
from markdown.util import etree
from markdown.extensions.toc import TocExtension

class WikiLinkExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        self.md = md
        WIKILINK_RE = r'\[\[(?P<target>[@\w/0-9:_ -]+)(?P<text>(?:\|[\w/0-9:_ -]+)?)\]\]'
        pattern = WikiLinks(WIKILINK_RE)
        pattern.md = md
        md.inlinePatterns.add('wikilink', pattern, "<not_strong")


class WikiLinks(Pattern):

    def handleMatch(self, m):
        target = m.group("target")
        text = m.group("text")
        text = text[1:] if text else None
        url, text = build_link(target, text)
        a = etree.Element('a')
        a.text = text
        a.set('href', url)
        return a

class readers(config):
    markdown = MarkdownReader(
        extensions=
        [ 'codehilite',
          'meta',
          TocExtension(),
          WikiLinkExtension(),
          'tables',
          'pymdownx.arithmatex',
          'pymdownx.superfences',
        ],
        extension_configs= {
            'codehilite': {
                'guess_lang': False,
                'linenums': True,
            },
            'pymdownx.arithmatex': {
                'generic': True,
            }
        },
        attrs = ('toc_tokens',)
    )
