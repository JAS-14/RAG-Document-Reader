import React , {useState,useEffect} from "react";
import "bootstrap/dist/css/bootstrap.css";
import axios from "axios"

function Chat() {
const [input,setInput]= useState({
  file:null,
  search:""
})
const [history,setHistory] = useState([])
const [response,setResponse] = useState([])
const [loading,setLoading] = useState(false)
const uploadFile = async () => {
  try {
      const formData = new FormData();
      formData.append("file", input.file);
      const token = localStorage.getItem("token")
      const res = await axios.post(
          "http://localhost:8000/Ask/upload",
          formData,
          {
              headers: {
                  "Content-Type": "multipart/form-data",
                  Authorization:`Bearer ${token}`
              },
          }
      );

      alert(res.data.message || "File uploaded successfully");
  } catch (err) {
      console.log(err.response?.data);
      alert("Upload failed");
  }
};

const search = async () => {
  setLoading(true)
  try {
    const token = localStorage.getItem("token");
      const res = await axios.post(
          "http://localhost:8000/Ask/search",
          {
              query: input.search,
          },
          {
            headers: {
                Authorization: `Bearer ${token}`,
            },
    }  );

      setResponse((prev)=>[...prev,{answer:res.data.answer,query:input.search},]);
      setInput({...input,search:''})
  } catch (err) {
      console.log(err.response?.data);
      alert("Search failed");
      setLoading(false)
  }
};

const gethistory = async()=>{
  try{
    const token = localStorage.getItem("token")
    const res = await axios.get('http://localhost:8000/Ask/history',{
      headers:{
        Authorization: `Bearer ${token}`
      },
    })
    setHistory(res.data)
  }catch(err){
    console.log(err.response?.data)
  }
}
const deleteHistory = async () => {
  try {
      const token = localStorage.getItem("token");

      await axios.delete(
          "http://localhost:8000/Ask/delete_history",
          {
              headers: {
                  Authorization: `Bearer ${token}`,
              },
          }
      );

      setHistory([]);
      alert("History deleted successfully");
  } catch (err) {
      console.log(err.response?.data);
  }
};
useEffect(()=>{
  gethistory()
},[])
  return (
    <div className="container-fluid p-4">
      <div className="row">
        <div className="col-lg-8">
          <div className="row align-items-center mb-3">
            <div className="col-md-9">
              <input
                type="text"
                placeholder="Ask anything..."
                className="form-control form-control-lg" name="search" value={input.search} onChange={(e)=>setInput({...input,search:e.target.value})}
              />
            </div>

            <div className="col-md-3">
              <button type="button" className="btn btn-primary w-100" onClick={search}>
                Search
              </button>
            </div>
          </div>
          <div className="row align-items-center mb-3">
          <div className="col-md-10">
          {/* File Upload */}
          <div className="mb-3">
            <input
              type="file"
              className="form-control form-control-lg" onChange={(e)=>setInput({...input,file:e.target.files[0]})}
            />
          </div>
          </div>
          <div className="col-md-2">
              <button type="button" className="btn btn-primary w-100" onClick={uploadFile}>
                Upload file
              </button>
              </div>
              </div>

          {/* Chat Area */}
          <div
            className="border rounded p-3"
            style={{ height: "500px", overflowY: "auto" }}
          >
            {loading && <p className="text-primary">Searching<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"   className={`bi bi-search ${loading ? "search-icon" : ""}`} viewBox="0 0 16 16">
  <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001q.044.06.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1 1 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0"/>
</svg></p>}
            {response.map((chat, index) => (
    <div key={index} className="mb-3">
        <div className="text-end bg-light w-20 rounded" style={{width:'30%',padding:'10px',marginLeft:'70%'}}>
            <strong>You:</strong>
            <p>{chat.query}</p>
        </div>

        <div  className="text-start bg-light w-20 rounded" style={{width:'80%',padding:'10px',margin:'10px'}}>
            <strong>AI:</strong>
            <p>{chat.answer}</p>
        </div>

        <hr />
    </div>
))}
          </div>
        </div>

        {/* Right Section */}
        <div className="col-lg-4" >
          <div className="border rounded p-3 bg-dark text-white">
            <h3>Chat History</h3>
            <button className="btn btn-danger" onClick={deleteHistory}>Clear</button>
            <hr />
            <ul className="list-group">
                {[...history].reverse().map((item)=>(
                  <li className="list-group-item"key={item.id}>{item.query}</li>
                ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Chat;