import html
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import quote, urlsplit


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1
        self.parts.append(' ')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden = max(0, self.hidden - 1)
        self.parts.append(' ')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain(value):
    parser = PlainText()
    parser.feed(value or '')
    return ' '.join(''.join(parser.parts).split())


def clock(value):
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def document(kind, data, book, base):
    if kind == 'book':
        book = data
        fallback = base + '/books/' + quote(data['slug'], safe='')
        body = plain(data.get('description_html') or data.get('description', ''))
    else:
        fallback = base + '/books/' + quote(book['slug'], safe='') + '/page/' + quote(data['slug'], safe='')
        body = plain(data.get('html') or data.get('raw_html') or data.get('text') or data.get('markdown', ''))
    url = data.get('url') or fallback
    actual, expected = urlsplit(url), urlsplit(base)
    if actual.scheme != 'https' or actual.netloc != expected.netloc:
        raise ValueError('Enlace de contenido fuera del origen autorizado')
    return dict(entity_type=kind, entity_id=int(data['id']), title=data['name'], body=body,
                url=url, book_id=int(book['id']), book_title=book['name'],
                source_at=clock(data.get('updated_at') or data.get('created_at') or '1970-01-01T00:00:00Z'))


def highlight(value):
    # PostgreSQL genera marcadores privados. Primero escapar TODO el origen,
    # luego permitir únicamente las etiquetas mark generadas por nosotros.
    return html.escape(value or '').replace('\ue000', '<mark>').replace('\ue001', '</mark>')


def hit(row):
    result = dict(entity_type=row['entity_type'], entity_id=row['entity_id'], title=row['title'],
                  url=row['url'], score=float(row['score']),
                  highlights={key: highlight(row['highlight_' + key]) for key in ('title', 'body', 'book_title')})
    if row['entity_type'] == 'page':
        result['book'] = dict(id=row['book_id'], title=row['book_title'])
    return result
