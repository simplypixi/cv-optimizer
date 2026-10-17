import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { UserRound, Briefcase, FileText, Plus, Trash2, Database } from 'lucide-react';
import { request, type Profile } from './api';
import Workflow from './Workflow';
import LinkedInImport from './LinkedInImport';
type Section = 'experiences'|'education'|'projects'|'skills';
const sections:Record<Section,string>={experiences:'Experience',education:'Education',projects:'Projects',skills:'Skills'};
const initialProfile={full_name:'',email:'',phone:'',location:'',headline:'',subtitle:'',summary:''};
export default function App(){
 const [profiles,setProfiles]=useState<Profile[]>([]);
 const [currentId,setCurrentId]=useState('');
 const [draft,setDraft]=useState(initialProfile);
 const [section,setSection]=useState<Section>('experiences');
 const [view,setView]=useState<'profile'|'workflow'>('profile');
 const [entry,setEntry]=useState<Record<string,string>>({});
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');
 const [notice,setNotice]=useState('');
 const current=profiles.find(x=>x.id===currentId);
 const load=useCallback(async(preferred?:string)=>{try{const rows=await request<Profile[]>('/profiles');setProfiles(rows);setCurrentId(old=>{const wanted=preferred||old;return rows.some(r=>r.id===wanted)?wanted:(rows[0]?.id||'')})}catch(e){setError(String(e))}},[]);
 useEffect(()=>{void load()},[load]);
 useEffect(()=>{if(current)setDraft({full_name:current.full_name,email:current.email||'',phone:current.phone||'',location:current.location||'',headline:current.headline||'',subtitle:current.subtitle||current.headline||'',summary:current.summary||''})},[current?.id]);
 async function perform(action:()=>Promise<unknown>,msg:string){setBusy(true);setError('');setNotice('');try{await action();await load(currentId);setNotice(msg)}catch(e){setError(e instanceof Error?e.message:String(e))}finally{setBusy(false)}}
 async function createProfile(e:FormEvent){e.preventDefault();setBusy(true);setError('');try{const row=await request<Profile>('/profiles','POST',{full_name:draft.full_name});await load(row.id);setNotice('Profile created')}catch(e){setError(String(e))}finally{setBusy(false)}}
 async function saveProfile(e:FormEvent){e.preventDefault();if(!current)return;await perform(()=>request(`/profiles/${current.id}`,'PATCH',{...draft,email:draft.email||null}), 'Profile saved')}
 async function addEntry(e:FormEvent){e.preventDefault();if(!current)return;
  const payload:Record<string,unknown>={...entry};for(const key of ['start_date','end_date']){if(payload[key]==='')payload[key]=null;else if(typeof payload[key]==='string')payload[key]=String(payload[key])+'-01'}
  await perform(async()=>{await request(`/profiles/${current.id}/${section}`,'POST',payload);setEntry({})},'Entry added');
 }
 async function removeEntry(id:string){if(!current||!confirm('Delete this entry?'))return;await perform(()=>request(`/profiles/${current.id}/${section}/${id}`,'DELETE'),'Entry removed')}
 const field=(name:string,placeholder:string,required=false,type='text')=><input aria-label={placeholder} type={type} required={required} placeholder={placeholder} value={entry[name]||''} onChange={e=>setEntry(d=>({...d,[name]:e.target.value}))}/>;
 return <div className="shell"><aside><div className="brand"><FileText size={25}/> CV Optimizer <small>LOCAL v1.0</small></div><nav><button className={view==='profile'?'nav active':'nav'} onClick={()=>setView('profile')}><UserRound size={18}/> My Profile</button><button className={view==='workflow'?'nav active':'nav'} onClick={()=>setView('workflow')}><Briefcase size={18}/> CV & ATS Analysis</button></nav><div className="aside-bottom"><Database size={16}/> Data stays on your computer</div></aside>
 <main><header><div><p className="eyebrow">CV OPTIMIZER / LOCAL</p><h1>{view==='profile'?'Your Professional Profile':'Job Analysis & CV Versions'}</h1><p className="muted">One source of verified experience, many tailored CVs.</p></div><div className="toolbar"><select aria-label="Select profile" value={currentId} onChange={e=>setCurrentId(e.target.value)}><option value="">Select profile</option>{profiles.map(x=><option key={x.id} value={x.id}>{x.full_name}</option>)}</select></div></header>
 {error&&<div className="alert error" role="alert">{error}</div>}{notice&&<div className="alert ok" role="status">{notice}</div>}
 {!current?<div className="card create"><h2>Create your first profile</h2><p className="muted">Start with your full name and complete the rest in the editor.</p><form onSubmit={createProfile}><input required aria-label="Full name" placeholder="Full name" value={draft.full_name} onChange={e=>setDraft(d=>({...d,full_name:e.target.value}))}/><button disabled={busy}><Plus size={17}/> Create profile</button></form></div>:view==='workflow'?<Workflow key={current.id} profile={current}/>:<>
 <LinkedInImport profile={current} onComplete={()=>load(current.id)}/>
 <section className="card"><div className="sectionhead"><h2>Basic Information</h2><span className="pill">Stored locally</span></div><form onSubmit={saveProfile}><div className="two"><label>Full name<input required value={draft.full_name} onChange={e=>setDraft(d=>({...d,full_name:e.target.value}))}/></label><label>Professional subtitle<input placeholder="np. Senior Fullstack Developer" value={draft.subtitle} onChange={e=>setDraft(d=>({...d,subtitle:e.target.value}))}/></label><label>E-mail<input type="email" value={draft.email} onChange={e=>setDraft(d=>({...d,email:e.target.value}))}/></label><label>Phone<input value={draft.phone} onChange={e=>setDraft(d=>({...d,phone:e.target.value}))}/></label><label>Location<input value={draft.location} onChange={e=>setDraft(d=>({...d,location:e.target.value}))}/></label></div><label>Professional summary<textarea rows={3} value={draft.summary} onChange={e=>setDraft(d=>({...d,summary:e.target.value}))}/></label><button disabled={busy}>Save basic information</button></form></section>
 <section className="card"><div className="sectionhead"><div><h2>Professional Links</h2><p className="muted">Optional. Add your website, GitHub, portfolio or any other link.</p></div></div>
 {current.links.map(link=><div className="entry" key={link.id}><div><strong>{link.label}</strong><p><a href={link.url} target="_blank" rel="noreferrer">{link.url}</a></p></div><button type="button" className="iconbtn" title="Remove link" onClick={()=>{void perform(()=>request(`/profiles/${current.id}/links/${link.id}`,'DELETE'),'Link removed')}}><Trash2 size={16}/></button></div>)}
 <LinkForm profileId={current.id} position={current.links.length} onSaved={()=>load(current.id)} />
 </section>
 <section className="card"><div className="sectionhead"><div><h2>Experience & Skills</h2><p className="muted">Only enter genuine experience and qualifications.</p></div></div><div className="tabs">{(Object.keys(sections) as Section[]).map(s=><button type="button" key={s} className={section===s?'tab selected':'tab'} onClick={()=>{setSection(s);setEntry({})}}>{sections[s]} ({current[s].length})</button>)}</div>
 <div className="entries">{current[section].length===0?<p className="muted empty">No entries in this section.</p>:current[section].map(item=><div className="entry" key={item.id}><div><strong>{'title' in item?item.title:'institution' in item?item.institution:'name' in item?item.name:''}</strong><p>{'company' in item?item.company:'description' in item?item.description:'evidence_note' in item?item.evidence_note:''}</p></div><button type="button" className="iconbtn" title="Remove" onClick={()=>removeEntry(item.id)}><Trash2 size={16}/></button></div>)}</div>
 <h3>Add entry</h3><form onSubmit={addEntry} className="entryform">{section==='experiences'&&<>{field('title','Job title',true)}{field('company','Company',true)}{field('start_date','Start date',true,'month')}{field('end_date','End date',false,'month')}<textarea placeholder="Description and achievements" value={entry.description||''} onChange={e=>setEntry(d=>({...d,description:e.target.value}))}/></>}{section==='education'&&<>{field('institution','School / University',true)}{field('degree','Degree / Field of study')}{field('start_date','Start date',false,'month')}{field('end_date','End date',false,'month')}<textarea placeholder="Opis" value={entry.description||''} onChange={e=>setEntry(d=>({...d,description:e.target.value}))}/></>}{section==='projects'&&<>{field('name','Project name',true)}{field('url','URL')}<textarea placeholder="Project description" value={entry.description||''} onChange={e=>setEntry(d=>({...d,description:e.target.value}))}/></>}{section==='skills'&&<>{field('name','Skill',true)}{field('category','Category')}<textarea placeholder="Evidence / example of use" value={entry.evidence_note||''} onChange={e=>setEntry(d=>({...d,evidence_note:e.target.value}))}/></>}<button disabled={busy}><Plus size={17}/> Dodaj {sections[section].toLowerCase()}</button></form>
 </section></>}
 </main></div>
}

function LinkForm({profileId,position,onSaved}:{profileId:string;position:number;onSaved:()=>Promise<void>}){
 const [label,setLabel]=useState('');const [url,setUrl]=useState('');const [error,setError]=useState('');const [busy,setBusy]=useState(false);
 async function submit(e:FormEvent){e.preventDefault();setError('');setBusy(true);try{await request(`/profiles/${profileId}/links`,'POST',{label,url,position});setLabel('');setUrl('');await onSaved()}catch(err){setError(String(err))}finally{setBusy(false)}}
 return <form onSubmit={submit} className="entryform"><div className="two"><label>Label<input required maxLength={100} placeholder="np. GitHub" value={label} onChange={e=>setLabel(e.target.value)}/></label><label>URL<input required type="url" placeholder="https://github.com/..." value={url} onChange={e=>setUrl(e.target.value)}/></label></div><button disabled={busy}><Plus size={17}/> Add link</button>{error&&<p role="alert" className="alert error">{error}</p>}</form>
}
