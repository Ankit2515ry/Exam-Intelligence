import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Send, Bot, User, LogOut } from 'lucide-react';
import { chatService, uploadService } from '../api/apiService';

export default function Chat() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const data = await uploadService.getDocuments();
        setDocuments(data);
        if (data.length > 0) setSelectedDocId(data[0].id); 
      } catch (err) {
        console.error(err);
      }
    };
    fetchDocs();
  }, []);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = { role: 'user', text: input };
    setMessages((prev) => [...prev, userMsg]);
    const currentInput = input;
    setInput("");
    setLoading(true);

    try {
      // Sends chat data contract payload down to FastAPI server
      const response = await chatService.sendMessage(currentInput, selectedDocId ? String(selectedDocId) : null);
      setMessages((prev) => [...prev, { role: 'bot', text: response.answer }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'bot', text: "Authentication or server context routing pipeline error." }]);
    } finally {
      setLoading(false);
    }
  };

  // SIGN OUT FUNCTION
  const handleSignOut = () => {
    localStorage.removeItem('userToken');
    navigate('/');
  };

  return (
    <div className="flex h-screen bg-slate-100">
      <aside className="w-64 bg-slate-900 text-white flex flex-col p-4 justify-between">
        <div className="space-y-6">
          <div className="text-xl font-bold px-2 tracking-wide">Exam Intelligence</div>
          <nav className="space-y-2">
            <Link to="/dashboard" className="flex items-center gap-3 text-slate-400 hover:bg-slate-800 hover:text-white px-4 py-2.5 rounded-lg font-medium transition"><LayoutDashboard size={20} /> Dashboard</Link>
            <Link to="/chat" className="flex items-center gap-3 bg-indigo-600 px-4 py-2.5 rounded-lg font-medium"><MessageSquare size={20} /> Chat Module</Link>
          </nav>
        </div>
        
        {/* Grounding Selection */}
        <div className="p-2 bg-slate-800 rounded-xl border border-slate-700 my-4">
          <label className="block text-xs font-semibold uppercase text-slate-400 tracking-wider mb-2">Grounding Document Target</label>
          <select value={selectedDocId} onChange={(e) => setSelectedDocId(e.target.value)} className="w-full bg-slate-900 text-white border border-slate-700 rounded-md p-1.5 text-xs focus:outline-none">
            <option value="">Global System Scope</option>
            {documents.map(doc => (
              <option key={doc.id} value={doc.id}>{doc.filename}</option>
            ))}
          </select>
        </div>

        {/* Added Sign Out Action Button */}
        <button 
          onClick={handleSignOut} 
          className="flex items-center gap-3 text-rose-400 hover:bg-rose-950/40 px-4 py-2.5 rounded-lg font-medium transition cursor-pointer text-left w-full mt-auto"
        >
          <LogOut size={20} /> Sign Out
        </button>
      </aside>

      <main className="flex-1 flex flex-col bg-white">
        <header className="border-b border-slate-200 p-4 shadow-xs">
          <h2 className="font-bold text-slate-800">AI Grounded Prompt Shell</h2>
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-slate-50">
          {messages.map((msg, index) => (
            <div key={index} className={`flex gap-3 max-w-2xl ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}>
              <div className={`p-2 rounded-full h-8 w-8 flex items-center justify-center border shrink-0 ${msg.role === 'user' ? 'bg-indigo-100 border-indigo-200 text-indigo-600' : 'bg-slate-100 border-slate-200 text-slate-600'}`}>
                {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className={`p-3 rounded-2xl text-sm leading-relaxed shadow-xs border ${msg.role === 'user' ? 'bg-indigo-600 border-indigo-700 text-white rounded-tr-none' : 'bg-white border-slate-200 text-slate-800 rounded-tl-none'}`}>
                {msg.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex gap-3 max-w-2xl">
              <div className="p-2 rounded-full h-8 w-8 flex items-center justify-center border bg-slate-100 border-slate-200 text-slate-600 animate-spin">
                <Bot size={16} />
              </div>
              <div className="p-3 rounded-2xl text-sm bg-white border border-slate-200 text-slate-400 italic rounded-tl-none">Agent is processing vectors...</div>
            </div>
          )}
        </div>

        <footer className="p-4 border-t border-slate-200 bg-white">
          <form onSubmit={handleSend} className="flex gap-2">
            <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Submit a question related to your active knowledge documents..." className="flex-1 border border-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm" />
            <button type="submit" disabled={loading} className="bg-indigo-600 text-white p-2.5 rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"><Send size={18} /></button>
          </form>
        </footer>
      </main>
    </div>
  );
}