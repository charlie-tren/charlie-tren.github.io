/* Dev test suite for lexicon.html - NOT part of the app. Run: node lexicon/test.js (or cd lexicon && node test.js)
   Loads the real <script> from lexicon.html under DOM stubs, then asserts. */
"use strict";
const fs=require("fs"), path=require("path");

// ---- DOM / browser stubs so the app script runs headless ----
global.localStorage={_d:{},getItem(k){return this._d[k]||null;},setItem(k,v){this._d[k]=String(v);}};
const el={focus(){},value:"",setSelectionRange(){},dataset:{},addEventListener(){},click(){},href:"",download:""};
global.document={getElementById(){return el;},addEventListener(){},createElement(){return el;}};
global.URL={createObjectURL(){return "blob:x";},revokeObjectURL(){}};
global.Blob=function(){};
global.alert=function(){};

const html=fs.readFileSync(path.join(__dirname,"index.html"),"utf8");
const body=html.split("<script>")[1].split("</script>")[0];

let pass=0, fail=0; const fails=[];
function A(cond,msg){ if(cond){pass++;} else {fail++; fails.push(msg);} }

const suite = `
;(function(){
  // ---- FSRS engine identities ----
  A(Math.abs(retr(1,1)-0.9)<1e-9, "R(S,S)=0.9");
  A(Math.abs(ivl(0.9,7)-7)<1e-6, "ivl(0.9,S)=S");
  A(ivl(0.8,10)>10 && ivl(0.95,10)<10, "lower retention -> longer interval");

  // ---- learning-step previews distinct for a new card ----
  var nc=newSub("new");
  var p=[1,2,3,4].map(function(g){return preview(nc,g,0.9,1825,0);});
  A(p[0]==="<10m" && p[1]==="10m" && p[2]==="1d" && p[3]==="4d", "new-card previews <10m/10m/1d/4d ("+p.join("/")+")");

  // ---- schedule: new + Good graduates to 1d review, stability seeded ----
  var g=schedule(newSub("new"),3,0.9,1825,0);
  A(g.card.state==="review" && g.card.stability===1 && g.card.lastInterval===1, "new+Good graduates to 1d");
  var e=schedule(newSub("new"),4,0.9,1825,0);
  A(e.card.state==="review" && e.card.stability===4, "new+Easy graduates to 4d");
  var ag=schedule(newSub("new"),1,0.9,1825,0);
  A(ag.card.state==="learning" && ag.learning===true, "new+Again -> learning (re-queue)");

  // ---- checkAnswer + blankExample ----
  A(checkAnswer("BATNA","batna")==="correct", "answer check case-insensitive");
  A(checkAnswer("plaintif","plaintiff")==="almost", "one typo -> almost");
  A(checkAnswer("zzz","plaintiff")==="wrong" && checkAnswer("","x")==="empty", "wrong/empty");
  A(blankExample("The plaintiff sued.","plaintiff").toLowerCase().indexOf("plaintiff")<0, "example blanks answer");
  A(lev("kitten","sitting")===3, "levenshtein basic");

  // ---- migration v1 -> v2 ----
  var m=migrateFlat({word:"foo",meaning:"m",state:"review",stability:9,difficulty:5,reps:6,lapses:1,lastInterval:22,due:1});
  A(m.fwd.state==="review" && m.fwd.stability===9 && m.rev.state==="new", "v1->v2 fwd carries, rev unlocked");
  A(migrateFlat({word:"b",meaning:"m",state:"new"}).rev.state==="locked", "v1->v2 unstudied rev locked");

  // ---- normCard handles both shapes ----
  var nv2=normCard({word:"w",meaning:"m",fwd:{state:"review",stability:3},rev:{state:"new"}});
  A(nv2.fwd.state==="review" && nv2.fwd.stability===3 && nv2.rev.state==="new", "normCard v2");
  var nv1=normCard({word:"w",meaning:"m",state:"learning",stability:2});
  A(nv1.fwd.state==="learning" && !!nv1.rev, "normCard v1-flat -> v2");

  // ---- done / finished thresholds (4 recalls & 30d gap) ----
  var mk=function(s,iv){return {state:"review",successes:s,lastInterval:iv};};
  A(subDone(mk(4,30))===true && subDone(mk(4,29))===false && subDone(mk(3,50))===false, "subDone = 4 recalls & >=30d");
  A(wordFinished({fwd:mk(4,31),rev:mk(4,31)})===true && wordFinished({fwd:mk(4,31),rev:mk(1,5)})===false, "wordFinished needs both");

  // ---- success counting, distinct-day, reverse unlock (live) ----
  var pc=state.cards.find(function(c){return c.word==="plaintiff";});
  pc.fwd.state="new"; pc.fwd.due=Date.now(); pc.rev.state="locked";
  ses.queue=[{id:pc.id,dir:"fwd"}]; ses.typed=""; ses.revealed=true;
  gradeCurrent(3);
  A(pc.fwd.successes===1, "success counted on pass");
  A(pc.rev.state==="new", "reverse unlocked after first fwd recall");
  pc.fwd.due=Date.now()-1; ses.queue=[{id:pc.id,dir:"fwd"}]; gradeCurrent(3);
  A(pc.fwd.successes===1, "same-day 2nd recall not double counted");

  // ---- inferred reverse grade mapping ----
  var pd=state.cards.find(function(c){return c.word==="deplore";});
  pd.rev.state="new"; pd.rev.due=Date.now(); ses.queue=[{id:pd.id,dir:"rev"}]; ses.typed="deplore"; ses.revealed=true;
  gradeReverse();
  A(pd.rev.state==="review" && pd.rev.successes===1, "reverse correct -> pass+graduate");
  pd.rev.state="review"; pd.rev.due=Date.now()-1; pd.rev.stability=8; pd.rev.lastReview=Date.now()-4*86400000;
  ses.queue=[{id:pd.id,dir:"rev"}]; ses.typed="qqqqq"; ses.revealed=true; gradeReverse();
  A(pd.rev.state==="relearning", "reverse wrong -> Again/relearning");

  // ---- session item lists build ----
  A(Array.isArray(dueItems()) && Array.isArray(newItems()), "due/new item lists");

  // ---- automatic backup ----
  A(state.settings.autoBackup===true, "autoBackup default on");
  state.backupDate=""; maybeBackup(); A(state.backupDate===todayKey(), "maybeBackup snapshots when none today");
  var bd=state.backupDate; maybeBackup(); A(state.backupDate===bd, "maybeBackup no-ops second time same day");
  state.settings.autoBackup=false; state.backupDate=""; maybeBackup(); A(state.backupDate==="", "maybeBackup skips when disabled");
  state.settings.autoBackup=true;

  // ---- storage persistence request is safe when unsupported ----
  A(typeof requestPersistence==="function", "requestPersistence defined");
  var threw=false; try{requestPersistence();}catch(e){threw=true;}
  A(threw===false, "requestPersistence never throws (no navigator.storage)");

  // ---- hub link lives in the toolbar ----
  A(header().indexOf("Other Projects")>=0 && header().indexOf("charlie-tren.github.io")>=0, "hub link in nav");
  A(header().indexOf("Other Projects")>header().indexOf("Settings"), "hub link sits after Settings");

  // ---- STABILITY FUZZ: 3000 random reviews, assert invariants never break ----
  var seed=987654321; function rnd(){seed=(seed*1103515245+12345)&0x7fffffff;return seed/0x7fffffff;}
  var VALID={learning:1,relearning:1,review:1}; var bad=0, t0=1e12;
  for(var i=0;i<3000;i++){
    var c=state.cards[Math.floor(rnd()*state.cards.length)];
    var dir=rnd()<0.5?"fwd":"rev";
    var sub=c[dir]; if(!sub||sub.state==="locked"||sub.state==="new"){ sub=newSub(rnd()<0.5?"new":"review"); if(sub.state==="review"){sub.stability=1+rnd()*40;sub.difficulty=1+rnd()*9;sub.lastReview=t0;} }
    var now=t0+Math.floor(rnd()*1e10);
    var G=1+Math.floor(rnd()*4);
    var o=schedule(sub,G,0.8+rnd()*0.17,1825,now);
    var s=o.card;
    if(!(Number.isFinite(s.stability)&&s.stability>=0)) bad++;
    if(!(Number.isFinite(s.difficulty)&&s.difficulty>=1&&s.difficulty<=10)) bad++;
    if(!(Number.isFinite(s.due)&&s.due>now)) bad++;
    if(!(Number.isFinite(s.lastInterval)&&s.lastInterval>=0&&s.lastInterval<=1825)) bad++;
    if(!VALID[s.state]) bad++;
    if(s.state==="review" && !(s.stability>0)) bad++;
  }
  A(bad===0, "fuzz: "+bad+" invariant breaks across 3000 random reviews");
  console.log("(deck built: "+state.cards.length+" cards)");
})();
`;

try{ eval(body+suite); }
catch(err){ fail++; fails.push("THREW: "+(err&&err.stack||err)); }

console.log("");
fails.forEach(function(f){ console.log("  FAIL: "+f); });
console.log((fail?"":"")+pass+" passed, "+fail+" failed");
process.exit(fail?1:0);
