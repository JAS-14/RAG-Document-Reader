import React,{useState} from "react";
import 'bootstrap/dist/css/bootstrap.css'
import {NavLink,useNavigate} from 'react-router-dom'
import axios from "axios"
function Signup(){
    const navigate = useNavigate()
    const [input,setInput] = useState({
        username:'',
        email:'',
        password:'',
    })
    const handleSubmit = async (e) => {
        e.preventDefault();
    
        try {
            await axios.post(
                "http://localhost:8000/auth/create-user",
                {
                    name: input.username,
                    email: input.email,
                    password: input.password,
                }
            );
    
            navigate("/");
    
        } catch (err) {
            console.log(err);
            alert("Signup failed");
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
                <h1 className="display-4 fw-bold">Create Account</h1>
                <p className="small text-primary fw-bold">Start and Unlock the power of AI-powered knowledge</p>
                <input type="text" className="form-control form-control-lg mt-4" placeholder="Name" onChange={handleChange} name="username" value={input.username}/>
                <input type="email" className="form-control form-control-lg mt-4" placeholder="Email" onChange={handleChange} name="email" value={input.email}/>
                <input type="password" className="form-control form-control-lg mt-4" placeholder="Password" onChange={handleChange} name="password" value={input.password}/>
                <input type="submit" className="btn btn-primary btn-lg d-flex w-100 mt-4" value="Signup"/>
                <p className="small text-center mt-3 fw-bold">Already has account?<NavLink to="/">Signin</NavLink></p>
            </form></div>
        </div>
    )
}
export default Signup;