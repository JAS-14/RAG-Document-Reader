import React,{useState} from "react";
import 'bootstrap/dist/css/bootstrap.css'
import {NavLink,useNavigate} from 'react-router-dom'
import axios from 'axios'

function Login(){
    const navigate = useNavigate()
    const [input,setInput] = useState({
        username:'',
        password:''
    })
    const handleSubmit = async(e)=>{
        e.preventDefault()
        try{
            const formData = new URLSearchParams()
            formData.append("username",input.username)
            formData.append("password",input.password)
            const res = await axios.post("http://localhost:8000/auth/token",formData,
                {
                    headers:{
                        "Content-Type":"application/x-www-form-urlencoded",
                    },
                }
            );
            console.log(res.data)
            localStorage.setItem("token",res.data.access_token)
            navigate("/chat")
        }
        catch (err) {
            console.log(err.response);
            console.log(err.response?.data);
        
            alert(err.response?.data?.detail || "Login failed");
        }
    };

                        const handleChange= (e)=>{
        const {name, value}= e.target;
        setInput({...input,[name]:value})
    }
    return(
        <div>
            <div className="container rounded" style={{backgroundColor:'rgba(255,255,255,0.2)',width:'500px',padding:'30px',color:'white',marginTop:'100px'}}>
                <form onSubmit={handleSubmit}>
                <h1 className="display-4 fw-bold">Sign in</h1>
                <p className="small text-primary fw-bold">Enter and Unlock the power of AI-powered knowledge</p>
                <input type="text" className="form-control form-control-lg mt-4" placeholder="Name" name="username" onChange={handleChange} value={input.username}/>
                <input type="password" className="form-control form-control-lg mt-4" placeholder="Password" name="password" onChange={handleChange} value={input.password}/>
                <input type="submit" className="btn btn-primary btn-lg d-flex w-100 mt-4" value="Login"/>
                <p className="small text-center mt-3 fw-bold">New User?<NavLink to="/signup">Signup</NavLink></p>
                </form>
            </div>
        </div>
    )
}
export default Login;