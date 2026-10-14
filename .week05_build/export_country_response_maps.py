"""Portable aggregate-only map regeneration using the existing offline page shells."""
from pathlib import Path
import argparse
import html
import json
import re

def export_response_maps(root, output, inline_dir=None):
    root,output=Path(root).resolve(),Path(output).resolve()
    docs=root/'docs' if (root/'docs').is_dir() else root/'github_publication/docs'
    tools=(root/'.week05_build/country-response-distance-tools.js').read_text()
    response=json.loads((output/'response_map_payload.json').read_text())
    d3=(docs/'vendor/d3.min.js').read_text()
    assert 'd3js.org v7.9.0' in d3[:200] and '</script' not in d3.lower()
    names=[('index.html','country-similarity-map-template.html','wrp-sim-data','__WRP_SIMILARITY_DATA__','wrp-mixture-similarity','country-similarity-fragment.html'),
           ('country-income.html','country-income-map-template.html','wrp-inc-data','__WRP_INCOME_DATA__','wrp-country-income','country-income-fragment.html')]
    for filename,template,identity,placeholder,root_id,source_name in names:
        path=docs/filename;document=path.read_text()
        match=re.search(r'data-srcdoc="(.*?)"',document,re.S);assert match
        inner=html.unescape(match.group(1))
        data=json.loads(re.search(r'<script id="'+identity+r'" type="application/json">(.*?)</script>',inner,re.S).group(1))
        assert [c['iso'] for c in data['countries']]==response['country_order']
        data['responses']=response
        fragment=(root/'.week05_build'/template).read_text().replace(placeholder,json.dumps(data,separators=(',',':'))).replace('__WRP_RESPONSE_TOOLS__',tools)
        assert len(fragment.encode())<1_000_000
        (docs/source_name).write_text(fragment)
        if inline_dir is not None:
            Path(inline_dir).mkdir(parents=True,exist_ok=True)
            inline_name='country-similarity-region-map.html' if filename=='index.html' else 'country-income-similarity.html'
            (Path(inline_dir)/inline_name).write_text(fragment)
        offline,count=re.subn(r'<script src="https://cdn\.jsdelivr\.net/npm/d3@7\.9\.0/dist/d3\.min\.js"></script>',lambda _:'<script>'+d3+'</script>',fragment)
        assert count==1
        start=inner.index('<div id="'+root_id+'">')
        controller=inner.index("const root=document.getElementById('"+root_id+"')",start)
        end=inner.index('</script>',controller)+len('</script>')
        # Replace the fragment's trailing whitespace as well, so repeated exports
        # do not grow the wrapper or alter hashes on each invocation.
        updated=inner[:start]+offline.rstrip()+"\n"+inner[end:].lstrip()
        assert not re.search(r'<script[^>]+src=',updated)
        path.write_text(document[:match.start(1)]+html.escape(updated,quote=True)+document[match.end(1):])
    return docs

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--inline-dir',type=Path)
    args=parser.parse_args()
    print('Prepared offline pages locally:',export_response_maps(args.root,args.output,args.inline_dir))
