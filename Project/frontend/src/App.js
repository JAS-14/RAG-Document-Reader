import React from "react"
import './App.css'
import {BrowserRouter, Routes , Route} from 'react-router-dom'
import Login from "./Components/Login"
import Signup from "./Components/Signup"
import Chat from "./Components/chat"
import { AuthProvider } from "./AuthContext"
import ProtectedRoute from "./Components/ProtectedRoute"

function App(){
    return(
        <div>
        <AuthProvider>
        <BrowserRouter>
        <Routes>
            <Route path="/" element={<Login/>}/>
            <Route path="/signup" element={<Signup/>}/>
            <Route
                path="/chat"
                element={
                    <ProtectedRoute>
                        <Chat/>
                    </ProtectedRoute>
                }
            />
        </Routes>
        </BrowserRouter>
        </AuthProvider>
        </div>
    )
}
export default App;