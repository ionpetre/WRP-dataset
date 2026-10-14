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
        rendered=document[:match.start(1)]+html.escape(updated,quote=True)+document[match.end(1):]
        header=(root/'.week05_build/research-page-header.html').read_text()
        current=filename=='index.html'
        title='How do worry and harm differ across countries?' if current else 'How do response patterns relate to country income?'
        description=('Compare 142 countries using worry and personal or known-person harm. Explore overall patterns or individual components.' if current else
                     'Explore country income groups and their response differences. Income provides context; it is not used to calculate country similarity.')
        replacements={'__PAGE_TITLE__':title,'__PAGE_DESCRIPTION__':description,
          '__COUNTRY_CLASS__':'is-current' if current else '', '__INCOME_CLASS__':'' if current else 'is-current',
          '__COUNTRY_CURRENT__':'aria-current="page"' if current else '', '__INCOME_CURRENT__':'' if current else 'aria-current="page"'}
        for key,value in replacements.items():header=header.replace(key,value)
        if '<header class="research-header">' in rendered:
            rendered=re.sub(r'<header class="research-header">.*?</header>',lambda _:header.rstrip(),rendered,count=1,flags=re.S)
        else:
            rendered=re.sub(r'<nav aria-label="Country maps">.*?</nav>',lambda _:header.rstrip(),rendered,count=1,flags=re.S)
        css=(root/'.week05_build/research-page-style.css').read_text()
        rendered=re.sub(r'<style>nav\{.*?</style>','',rendered,count=1,flags=re.S)
        if '<style id="wrp-research-page-style">' in rendered:
            rendered=re.sub(r'<style id="wrp-research-page-style">.*?</style>',lambda _:'<style id="wrp-research-page-style">'+css+'</style>',rendered,count=1,flags=re.S)
        else:rendered=rendered.replace('</head>','<style id="wrp-research-page-style">'+css+'</style>\n</head>',1)
        rendered=re.sub(r'<title>[^<]*</title>',lambda _:'<title>'+title+' · World Risk Poll</title>',rendered,count=1)
        path.write_text(rendered)
    return docs

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--inline-dir',type=Path)
    args=parser.parse_args()
    print('Prepared offline pages locally:',export_response_maps(args.root,args.output,args.inline_dir))
