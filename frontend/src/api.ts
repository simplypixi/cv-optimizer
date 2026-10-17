export type Experience = { id:string; company:string; title:string; start_date:string; end_date:string|null; description:string|null };
export type Education = { id:string; institution:string; degree:string|null; start_date:string|null; end_date:string|null; description:string|null };
export type Project = { id:string; name:string; description:string|null; url:string|null };
export type Skill = { id:string; name:string; category:string|null; evidence_note:string|null };
export type ProfileLink = {id:string;label:string;url:string;position:number};
export type Profile = { id:string; full_name:string; email:string|null; phone:string|null; location:string|null; headline:string|null; subtitle:string|null; links:ProfileLink[]; summary:string|null; experiences:Experience[]; education:Education[]; projects:Project[]; skills:Skill[] };
const API='/api/v1';
export async function request<T>(path:string, method='GET', body?:unknown): Promise<T> {
 const res=await fetch(API+path,{method,headers:body?{'Content-Type':'application/json'}:undefined,body:body?JSON.stringify(body):undefined});
 if(!res.ok){let msg=`HTTP ${res.status}`;try{const data=await res.json();msg=typeof data.detail==='string'?data.detail:JSON.stringify(data.detail)}catch{}throw new Error(msg)}
 if(res.status===204) return undefined as T;
 return res.json() as Promise<T>;
}
