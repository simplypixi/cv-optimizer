"""Human-readable, non-destructive comparison of stored CV JSON snapshots."""
from difflib import SequenceMatcher

LABELS = {'full_name':'Imię i nazwisko','subtitle':'Rola zawodowa','summary':'Podsumowanie',
          'email':'E-mail','phone':'Telefon','location':'Lokalizacja','links':'Linki',
          'experiences':'Doświadczenie','education':'Edukacja','projects':'Projekty',
          'skills':'Umiejętności','languages':'Języki','template':'Szablon','career_path':'Ścieżka kariery'}
EXCLUDED = {'id','profile_id','created_at','updated_at'}

def flat(value, path=''):
    result={}
    if isinstance(value,dict):
        for key, child in value.items():
            if key in EXCLUDED: continue
            result.update(flat(child, f'{path} / {LABELS.get(key,key)}' if path else LABELS.get(key,key)))
    elif isinstance(value,list):
        # Use stable IDs for pairing, but display meaningful descriptors independent of ordering.
        for index, child in enumerate(value):
            if isinstance(child,dict):
                caption=child.get('company') and (str(child['company'])+' — '+str(child.get('title',''))) or child.get('name') or child.get('institution') or child.get('label') or child.get('title')
                label=str(caption or f'Pozycja {index+1}')
                # Disambiguate repeated positions using stable IDs when present.
                key=f'{path} / {label}'
                if key in result: key+=f' [{index+1}]'
                result.update(flat(child,key))
            else: result[f'{path} / {index+1}']=str(child)
    elif value is not None and value != '': result[path]=str(value) if not isinstance(value,bool) else ('Tak' if value else 'Nie')
    return result

def compare_content(before,after):
    old,new=flat(before),flat(after)
    items=[]
    for path in sorted(old.keys()|new.keys() ,key=str.casefold):
        left,right=old.get(path),new.get(path)
        if left==right: continue
        kind='added' if left is None else 'removed' if right is None else 'changed'
        changes=[]
        if kind=='changed':
            for tag,i,j,k,l in SequenceMatcher(None,left.splitlines(),right.splitlines(),autojunk=False).get_opcodes():
                if tag!='equal':changes.append({'kind':tag,'before':left.splitlines()[i:j],'after':right.splitlines()[k:l]})
        items.append({'path':path,'kind':kind,'before':left,'after':right,'line_changes':changes})
    return {'changes':items,'counts':{k:sum(x['kind']==k for x in items) for k in ('added','removed','changed')}, 'note':'Porównanie zapisanych danych CV; nie jest porównaniem wyglądu plików PDF.'}
