import React,{useState} from "react";
import 'bootstrap/dist/css/bootstrap.css'
import {NavLink,useNavigate} from 'react-router-dom'
import api from "../api"
import './style.css'
function Signup(){
    const navigate = useNavigate()
    const [signup,setSignup] = useState(false)
    const [input,setInput] = useState({
        username:'',
        email:'',
        password:'',
    })
    const handleSubmit = async (e) => {
        setSignup(true)
        e.preventDefault();
    
        try {
            await api.post(
                "/auth/create-user",
                {
                    name: input.username,
                    email: input.email,
                    password: input.password,
                }
            );
    
            navigate("/");
            setSignup(false)
    
        } catch (err) {
            console.log(err);
            console.error("Signup failed");
            setSignup(false)
        }
    };
    const handleChange= (e)=>{
        const {name, value}= e.target;
        setInput({...input,[name]:value})
    }
    return(
        <div>
            {!signup &&
            <div className="container rounded" style={{backgroundColor:'rgba(255,255,255,0.2)',width:'500px',padding:'30px',color:'white',marginTop:'100px'}}>
               <form onSubmit={handleSubmit}>
                <h1 className="display-4 fw-bold">Create Account</h1>
                <p className="small text-primary fw-bold">Start and Unlock the power of AI-powered knowledge</p>
                <input type="text" className="form-control form-control-lg mt-4" placeholder="Name" onChange={handleChange} name="username" value={input.username}/>
                <input type="email" className="form-control form-control-lg mt-4" placeholder="Email" onChange={handleChange} name="email" value={input.email}/>
                <input type="password" className="form-control form-control-lg mt-4" placeholder="Password" onChange={handleChange} name="password" value={input.password}/>
                <input type="submit" className="btn btn-primary btn-lg d-flex w-100 mt-4" value="Signup"/>
                <p className="small text-center mt-3 fw-bold">Already has account?<NavLink to="/">Signin</NavLink></p>
            </form></div>
}
{signup &&

<p className="text-primary d-flex align-items-center">
<span className="thinking-dots thinking-dots loading-overlay thinking-dots-lg">
  <span></span>
  <span></span>
  <span></span>
</span>
</p>
}
        </div>
    )
}
export default Signup;