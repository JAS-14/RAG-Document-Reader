import React, { useState, useEffect } from "react";
import "bootstrap/dist/css/bootstrap.css";
import api from "../api";
import ReactMarkdown from "react-markdown";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";
import './style.css'

function Chat() {
  const navigate = useNavigate();
  const { token, logout } = useAuth();

  const [input, setInput] = useState({
    file: null,
    search: "",
  });
  const [history, setHistory] = useState([]);
  const [response, setResponse] = useState([]);
  const [loading, setLoading] = useState(false);

  const authHeader = { Authorization: `Bearer ${token}` };

  const uploadFile = async () => {
    try {
      const formData = new FormData();
      formData.append("file", input.file);
      const res = await api.post("/Ask/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
          ...authHeader,
        },
      });

      console.log(res.data.message || "File uploaded successfully");
    } catch (err) {
      console.log(err.response?.data);
    console.log("Upload failed");
    }
  };

  const search = async () => {
    setLoading(true);
    try {
      const res = await api.post(
        "/Ask/search",
        {
          query: input.search,
        },
        {
          headers: authHeader,
        }
      );

      // /Ask/search returns { query, answer, sources }, where sources is an
      // array of { label, source, page, snippet, relevance_score } used for
      // citations.
      setResponse((prev) => [
        ...prev,
        {
          answer: res.data.answer,
          query: input.search,
          sources: res.data.sources || [],
        },
      ]);
      setInput({ ...input, search: "" });

      // Refresh the history sidebar so the query just asked shows up right
      // away, instead of only appearing after a manual page refresh.
      // Refetching (rather than pushing a fake local entry) also picks up
      // the real DB id from the backend, which the list needs as its React key.
      gethistory();
    } catch (err) {
      console.log(err.response?.data);
      console.log("Search failed");
    } finally {
      setLoading(false);
    }
  };

  const gethistory = async () => {
    try {
      const res = await api.get("/Ask/history", {
        headers: authHeader,
      });
      setHistory(res.data);
    } catch (err) {
      console.log(err.response?.data);
    }
  };

  const deleteHistory = async () => {
    try {
      await api.delete("/Ask/delete_history", {
        headers: authHeader,
      });

      setHistory([]);
      console.log("History deleted successfully");
    } catch (err) {
      console.log(err.response?.data);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  useEffect(() => {
    gethistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="container-fluid p-4">
      <div className="row">
        <div className="col-lg-8">
          <div className="d-flex justify-content-end mb-2">
            <button type="button" className="btn btn-outline-light btn-sm" onClick={handleLogout}>
              Logout
            </button>
          </div>
          <div className="row align-items-center mb-3">
            <div className="col-md-9">
              <input
                type="text"
                placeholder="Ask anything..."
                className="form-control form-control-lg"
                name="search"
                value={input.search}
                onChange={(e) => setInput({ ...input, search: e.target.value })}
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
                  className="form-control form-control-lg"
                  onChange={(e) => setInput({ ...input, file: e.target.files[0] })}
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
            {!loading &&
              [...response].reverse().map((chat, index) => (
                <div key={index} className="mb-3">
                  <div
                    className="text-end bg-dark text-white w-20 rounded"
                    style={{ width: "30%", padding: "10px", marginLeft: "70%" }}
                  >
                    <strong>You:</strong>
                    <p>{chat.query}</p>
                  </div>
 
                  <div
                    className="text-start  bg-dark text-white w-20 rounded"
                    style={{ width: "80%", padding: "10px", margin: "10px" }}
                  >
                    <strong>AI:</strong>
                    <div className="markdown-body">
                      <ReactMarkdown>{chat.answer}</ReactMarkdown>
                    </div>
 
                    {chat.sources && chat.sources.length > 0 && (
                      <div className="mt-2 pt-2 border-top">
                        <small className="text-muted d-block mb-1">Sources</small>
                        {chat.sources.map((src) => (
                          <span
                            key={src.label}
                            className="badge bg-secondary me-1"
                            title={src.snippet}
                          >
                            {src.label} {src.source} (p.{src.page})
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
 
                  <hr />
                </div>
              ))}
 
            {loading && (
              <div className="d-flex justify-content-center align-items-center h-100">
                <span className="thinking-dots thinking-dots-lg loading">
                  <span></span>
                  <span></span>
                  <span></span>
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Right Section */}
        <div className="col-lg-4">
          <div className="border rounded p-3  bg-dark text-white">
            <h3>Chat History  <button className="btn btn-danger" onClick={deleteHistory}>
              Clear
            </button></h3>
            <hr />
            <ul className="list-group">
              {[...history].reverse().map((item) => (
                <li className="list-group-item" key={item.id}>
                  {item.query}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Chat;