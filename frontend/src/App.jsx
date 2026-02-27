import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, 
  Upload, 
  FileText, 
  ShieldCheck, 
  Loader2, 
  AlertCircle,
  CheckCircle2
} from 'lucide-react';

const App = () => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hello! I'm CognitoDoc. Upload a PDF and I'll help you analyze it using RAG architecture." }
  ]);
  const [input, setInput] = useState('');
  const [documents, setDocuments] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [connectionError, setConnectionError] = useState(false);
  const scrollRef = useRef(null);

  const API_BASE = "http://localhost:8000";

  // Auto-scroll chat
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  // Check if backend is alive
  useEffect(() => {
    fetch(API_BASE)
      .then(() => setConnectionError(false))
      .catch(() => setConnectionError(true));
  }, []);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;

    const userQuery = input;
    setMessages(prev => [...prev, { role: 'user', content: userQuery }]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userQuery }),
      });

      const data = await response.json();
      
      if (response.ok) {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: data.answer,
          citation: data.sources?.length > 0 ? `Sources: ${data.sources.join(', ')}` : null
        }]);
      } else {
        throw new Error(data.detail || "Chat failed");
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Error: I couldn't reach the backend. Make sure main.py is running." }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        setDocuments(prev => [...prev, { id: Date.now(), name: file.name }]);
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: `✅ "${file.name}" has been indexed into the vector database. You can now ask questions!` 
        }]);
      } else {
        alert("Upload failed. Check backend console.");
      }
    } catch (err) {
      alert("Could not connect to backend to upload.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      
      {/* SIDEBAR */}
      <aside className="w-96 bg-slate-900 border-r border-slate-800 flex flex-col flex-shrink-0 overflow-hidden">
        <div className="p-6 border-b border-slate-800 flex items-center gap-3 flex-shrink-0">
          <ShieldCheck className="text-emerald-400 w-8 h-8" />
          <h1 className="text-xl font-bold">Cognito<span className="text-emerald-400">Doc</span></h1>
        </div>

        <div className="p-4 flex-1 overflow-y-auto min-h-0">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Knowledge Base</h2>
            <label className="cursor-pointer p-1 hover:bg-slate-800 rounded text-emerald-400 flex-shrink-0">
              <Upload size={18} />
              <input type="file" className="hidden" onChange={handleFileUpload} accept=".pdf" />
            </label>
          </div>

          <div className="space-y-2">
            {documents.map(doc => (
              <div key={doc.id} className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:bg-slate-800/70 transition-colors">
                <FileText size={16} className="text-emerald-400 flex-shrink-0" />
                <span className="text-xs truncate font-medium flex-1">{doc.name}</span>
                <CheckCircle2 size={12} className="text-emerald-500 flex-shrink-0" />
              </div>
            ))}
            {isUploading && (
              <div className="flex items-center gap-3 p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20 animate-pulse">
                <Loader2 size={16} className="text-emerald-400 animate-spin flex-shrink-0" />
                <span className="text-xs text-emerald-400">Embedding...</span>
              </div>
            )}
            {documents.length === 0 && !isUploading && (
              <p className="text-xs text-slate-500 text-center py-8 italic">No documents uploaded yet</p>
            )}
          </div>
        </div>

        {connectionError && (
          <div className="p-4 bg-red-500/10 border-t border-red-500/20 flex items-center gap-2 text-red-400 text-xs flex-shrink-0">
            <AlertCircle size={14} className="flex-shrink-0" /> Backend Offline
          </div>
        )}
      </aside>

      {/* CHAT */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-8 py-6 flex flex-col">
          <div className="flex flex-col gap-6">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
                <div className={`rounded-2xl px-6 py-4 max-w-3xl ${
                  msg.role === 'user' ? 'bg-emerald-600 text-white rounded-br-none' : 'bg-slate-800 border border-slate-700 rounded-bl-none'
                }`}>
                  <p className="text-sm md:text-base leading-relaxed break-words">{msg.content}</p>
                  {msg.citation && (
                    <p className="mt-3 text-[10px] text-emerald-400 font-bold uppercase tracking-tight">{msg.citation}</p>
                  )}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <div className="flex gap-2 p-4 bg-slate-800 rounded-2xl rounded-bl-none">
                  <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                  <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                </div>
              </div>
            )}
          </div>
        </div>

        <form onSubmit={handleSendMessage} className="flex-shrink-0 bg-slate-950 border-t border-slate-800 px-8 py-6">
          <div className="max-w-full">
            <div className="relative">
              <input 
                type="text" 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Query your knowledge base..."
                className="w-full bg-slate-900 border border-slate-800 rounded-xl py-3 md:py-4 pl-5 md:pl-6 pr-12 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all text-sm md:text-base"
              />
              <button 
                type="submit" 
                disabled={isTyping || isUploading}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-emerald-400 hover:text-emerald-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send size={20} />
              </button>
            </div>
            <p className="text-center text-[10px] text-slate-600 mt-3 uppercase tracking-wider">
              Powered by RAG & Gemini
            </p>
          </div>
        </form>
      </main>
    </div>
  );
};

export default App;