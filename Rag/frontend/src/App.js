import React from "react"
import './App.css'
import {BrowserRouter, Routes , Route} from 'react-router-dom'
import Login from "./Components/Login"
import Signup from "./Components/Signup"
import Chat from "./Components/chat"
function App(){
    return(
        <div>
<BrowserRouter>
<Routes>
    <Route path="/" element={<Login/>}/>
    <Route path="/signup" element={<Signup/>}/>
    <Route path="/chat" element={<Chat/>}/>
</Routes>
</BrowserRouter>
</div>
    )
}
export default App;