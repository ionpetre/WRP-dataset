"""Check links as GitHub Pages resolves them, not as the repository filesystem does."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, unquote
import argparse
import json

SITE='https://ionpetre.github.io/WRP-dataset/'
REPOSITORY='https://github.com/ionpetre/WRP-dataset'

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
    def handle_starttag(self, tag, attrs):
        attributes=dict(attrs)
        if tag=='a' and 'href' in attributes:
            self.links.append(attributes['href'])
        # Inspect the offline maps' embedded documents as well as page chrome.
        for key in ['srcdoc','data-srcdoc']:
            if key in attributes:
                nested=Links()
                nested.feed(attributes[key])
                self.links.extend(nested.links)

def check(root):
    root=Path(root).resolve()
    public=root if (root/'docs').is_dir() else root/'github_publication'
    count=0
    supporting=set()
    for filename in ['index.html','countries.html','country-income.html']:
        parser=Links()
        parser.feed((public/'docs'/filename).read_text())
        for href in parser.links:
            if href.startswith('#'):
                continue
            resolved=urljoin(SITE+filename,href)
            if resolved.startswith(REPOSITORY+'/blob/main/'):
                relative=unquote(urlparse(resolved).path.split('/blob/main/',1)[1])
                assert (public/relative).is_file(), (filename,href,'Missing repository file')
                supporting.add(relative)
            elif urlparse(resolved).netloc==urlparse(SITE).netloc:
                assert resolved.startswith(SITE), (filename,href,'Escapes project Pages root')
                relative=unquote(urlparse(resolved).path[len(urlparse(SITE).path):])
                assert (public/'docs'/relative).is_file(), (filename,href,'Not inside Pages publication directory')
            else:
                assert resolved==REPOSITORY, (filename,href,'Unexpected external link')
            count+=1
    required={'research/METHODS.md','research/RESULTS.md',
        'course_artifacts/week05_frozen_objective1_v1/123d248adda6115f/development_original_category_profiles.csv'}
    assert supporting==required
    return {'passed':True,'pages':3,'links_checked':count,
        'github_pages_root':SITE,'supporting_repository_files':sorted(supporting)}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    args=parser.parse_args()
    print(json.dumps(check(args.root),indent=2))
