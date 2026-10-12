from pathlib import Path
import json
import frozen_transfer as a

root=Path(__file__).resolve().parent.parent
info=json.loads((root/'.week05_build/transfer_run.json').read_text())
namespace=vars(a).copy()
exec((root/'.week05_build/transfer_documentation.py').read_text(),namespace)
package,output=root/info['package_directory'],root/info['output_directory']
tables=namespace['transfer_reporting_tables'](root,package,output)
figures=namespace['plot_transfer_figures'](root,package,output)
print('Reporting complete; figures:',[p.name for p in figures],flush=True)
print('No model, frozen threshold or original transfer table was changed.',flush=True)
