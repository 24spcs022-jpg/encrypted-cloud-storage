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

let user = document.getElementById("luser").value
let pass = document.getElementById("lpass").value

let f = new FormData()
f.append("username", user)
f.append("password", pass)

fetch("/login",{method:"POST",body:f})
.then(r=>r.json())
.then(d=>{

console.log("PASSWORD LOGIN:", d)

if(d.token){
localStorage.setItem("user",user)
localStorage.setItem("token",d.token)
window.location="/dashboard"
}else{
alert(d.error)
}

})

}
let generatedOTP = ""

function sendOTP(){

let u = luser.value

if(!u){
alert("Enter username")
return
}

generatedOTP = Math.floor(1000 + Math.random()*9000).toString()

alert("OTP: " + generatedOTP)

document.getElementById("otpBox").style.display="block"
}

function verifyOTP(){

let entered = document.getElementById("otp").value
let user = document.getElementById("luser").value

if(!entered){
alert("Enter OTP")
return
}

if(entered !== generatedOTP){
alert("Wrong OTP ❌")
return
}

let f = new FormData()
f.append("username", user)

fetch("/login",{method:"POST",body:f})
.then(r=>r.json())
.then(d=>{

console.log("OTP LOGIN:", d)

if(d.token){
localStorage.setItem("user",user)
localStorage.setItem("token",d.token)
window.location="/dashboard"
}else{
alert("Login failed ❌")
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
