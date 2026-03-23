alert("JS Working");
const API="http://127.0.0.1:5000";

function register(){
fetch(API+"/register",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({username:ruser.value,password:rpass.value})
})
.then(r=>r.json()).then(d=>alert(d.msg));
}

function login(){

let f = new FormData()

f.append("username", luser.value)
f.append("password", lpass.value)

fetch("/login",{method:"POST",body:f})
.then(r=>r.json())
.then(d=>{

if(d.token){
localStorage.setItem("user",luser.value)
localStorage.setItem("token",d.token)
window.location="/dashboard"
}else{
alert(d.error)
}

})
}

function upload(){
let fd=new FormData();
fd.append("file",file.files[0]);
fd.append("password",upass.value);

fetch(API+"/upload",{
method:"POST",
headers:{token:localStorage.token},
body:fd
})
.then(r=>r.json()).then(d=>alert(d.msg));
}

function loadDash(){
fetch(API+"/dashboard",{headers:{token:localStorage.token}})
.then(r=>r.json())
.then(d=>out.innerHTML="Files: "+d.total_files);
}
