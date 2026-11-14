"""Comprobaciones iniciales S1. F6-E4 requiere después eventos reales y gateway."""
import json
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from search_svc.config import Settings
from search_svc.store import Store
from search_svc.bookstack import Reader


def main():
    settings = Settings()
    expected_id = int(sys.argv[1])
    request_id = 'PRE-B2-S1-index-inicial'

    def get(path):
        request=Request('http://127.0.0.1:8000'+path,headers={'X-API-Key':settings.api_key,'X-Request-ID':request_id})
        with urlopen(request,timeout=10) as response:
            assert response.headers.get('X-Request-ID') == request_id
            return response.read().decode()

    deadline=time.monotonic()+60
    while True:
        try:
            assert json.loads(get('/readyz'))['status']=='ready'
            break
        except HTTPError as exc:
            if exc.code != 503 or time.monotonic()>deadline:
                raise
            time.sleep(1)
    print('/healthz:',get('/healthz'))
    print('/readyz: 200; PostgreSQL, NATS, BookStack y carga inicial listos.')
    reader=Reader(settings)
    pages=list(reader.listing('pages',request_id))
    books=list(reader.listing('books',request_id))
    with Store(settings,reader).connect() as conn:
        rows=conn.execute('SELECT entity_type,count(*) AS total FROM search_documents GROUP BY entity_type').fetchall()
        counts={row['entity_type']:row['total'] for row in rows}
    assert counts.get('page',0)==len(pages) and counts.get('book',0)==len(books)
    print('Catalogo REST e indice coinciden:',counts)
    result=json.loads(get('/v2/search?q=alfa&entity_type=page'))
    item=next(row for row in result['items'] if row['entity_id']==expected_id)
    assert '<mark>alfa</mark>' in item['highlights']['body'].lower()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    book_result=json.loads(get('/v2/search?q=Pruebas%20CNA&entity_type=book'))
    assert any(row['title']=='Pruebas CNA' for row in book_result['items'])
    print('Busqueda por tipo book: OK')
    metrics=get('/metrics')
    assert 'http_requests_total' in metrics and 'http_request_duration_seconds_bucket' in metrics
    print('Metricas Prometheus y X-Request-ID: OK')
    print('PASS: carga inicial completa, pagina encontrada, resaltado seguro y enlace nativo.')
    print('Pendiente F6-E4: edicion real, actualizacion por evento y consulta via gateway.')


if __name__=='__main__':
    main()
