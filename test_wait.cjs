const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/index.html','utf8');
let tick,expire,cleared=0;
const ctx={AbortController,performance:{now:()=>17000},console:{info:()=>{}},setInterval:f=>(tick=f,1),setTimeout:f=>(expire=f,2),clearInterval:()=>cleared++,clearTimeout:()=>cleared++};
vm.createContext(ctx);vm.runInContext(html.slice(html.indexOf('async function aiRequest('),html.indexOf('function saveDraft(')),ctx);
(async()=>{
 ctx.fetch=async(_,opts)=>new Promise((resolve,reject)=>opts.signal.addEventListener('abort',()=>reject(Object.assign(Error(),{name:'AbortError'}))));
 const target={isConnected:true};const pending=ctx.aiRequest('/test',{},target,'处理中');tick();assert(target.textContent.includes('最长等待 60 秒'));expire();await assert.rejects(pending,/60 秒/);assert.equal(cleared,2);
 console.log('PASS loading status, timeout feedback and timer cleanup');
})().catch(e=>{console.error(e);process.exitCode=1});
