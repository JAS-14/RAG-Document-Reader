import React,{useState} from "react";
import 'bootstrap/dist/css/bootstrap.css'
import {NavLink,useNavigate} from 'react-router-dom'
import api from '../api'
import { useAuth } from '../AuthContext'
import './style.css'

function Login(){
    const navigate = useNavigate()
    const { login } = useAuth()
    const [log , setLog] = useState(false)
    const [input,setInput] = useState({
        username:'',
        password:''
    })
    const handleSubmit = async(e)=>{
        setLog(true)
        e.preventDefault()
        try{
            const formData = new URLSearchParams()
            formData.append("username",input.username)
            formData.append("password",input.password)
            const res = await api.post("/auth/token",formData,
                {
                    headers:{
                        "Content-Type":"application/x-www-form-urlencoded",
                    },
                }
            );
            console.log(res.data)
            // Token lives only in AuthContext (React state), not
            // localStorage -- this is what makes a page refresh always land
            // back on the login page instead of silently staying signed in.
            login(res.data.access_token)
            navigate("/chat")
            setLog(false)
        }
        catch (err) {
            console.log(err.response);
            console.log(err.response?.data);
            setLog(false)
            console.error(err.response?.data?.detail || "Login failed");
        }
    };

                        const handleChange= (e)=>{
        const {name, value}= e.target;
        setInput({...input,[name]:value})
    }
    return(
        <div>
            {!log &&
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
}
{log &&

<p className="text-primary d-flex align-items-center">
<span className="thinking-dots loading-overlay thinking-dots-lg">
  <span></span>
  <span></span>
  <span></span>
</span>
</p>
}
        </div>
    )
}
export default Login;