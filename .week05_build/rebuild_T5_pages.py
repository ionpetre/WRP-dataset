"""Rebuild the offline map wrappers from editable fragments. No data or fitting."""
from pathlib import Path
import html
import re

ROOT=Path(__file__).resolve().parents[1]
helper=(ROOT/'.week05_build/T5-response-distance-tools.js').read_text()
for page,fragment in [('countries.html','country-similarity-fragment.html'),
                      ('country-income.html','country-income-fragment.html')]:
    path=ROOT/'docs'/page
    text=(ROOT/'docs'/fragment).read_text()
    text=re.sub(r'(<script id="wrp-response-tools">).*?(</script>)',
                lambda m:m[1]+helper+m[2],text,flags=re.S)
    (ROOT/'docs'/fragment).write_text(text)
    document=path.read_text()
    match=re.search(r'data-srcdoc="(.*?)"',document,re.S)
    inner=html.unescape(match[1])
    root_id='wrp-mixture-similarity' if page=='countries.html' else 'wrp-country-income'
    start=inner.index('<div id="'+root_id+'">')
    tail=inner.index("const root=document.getElementById('")+len("const root=document.getElementById('")
    end=inner.index('</script>',tail)+len('</script>')
    inner=inner[:start]+text.rstrip()+'\n'+inner[end:].lstrip()
    path.write_text(document[:match.start(1)]+html.escape(inner,quote=True)+document[match.end(1):])
    print('Rebuilt',page)
