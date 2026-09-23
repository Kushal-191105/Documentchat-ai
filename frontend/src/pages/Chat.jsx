import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import api from '../api';

const Chat = () => {
  const { documentId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    initChat();
  }, [documentId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const initChat = async () => {
    try {
      // 1. Check if a session already exists for this document
      const res = await api.get('chat/sessions/');
      const existingSession = res.data.find(s => s.document === parseInt(documentId));
      
      let sessionId;
      if (existingSession) {
        sessionId = existingSession.id;
        setSession(existingSession);
      } else {
        // 2. Create a new session
        const newSessionRes = await api.post('chat/sessions/', { document: documentId });
        sessionId = newSessionRes.data.id;
        setSession(newSessionRes.data);
      }

      // 3. Load messages
      const msgsRes = await api.get(`chat/sessions/${sessionId}/messages/`);
      setMessages(msgsRes.data);
    } catch (error) {
      console.error("Failed to initialize chat", error);
      if (error.response?.status === 401) navigate('/login');
    }
  };

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim() || !session) return;

    const userMessage = { id: Date.now(), role: 'user', content: question };
    setMessages(prev => [...prev, userMessage]);
    setQuestion('');
    setLoading(true);

    const startTime = Date.now();

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/chat/sessions/${session.id}/ask/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ question: userMessage.content })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setLoading(false); // Stop loading animation immediately as stream starts
      
      const aiMessageId = Date.now();
      setMessages(prev => [...prev, { id: aiMessageId, role: 'ai', content: '' }]);

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.substring(6);
            if (dataStr === '[DONE]') {
              const totalTime = ((Date.now() - startTime) / 1000).toFixed(2);
              setMessages(prev => prev.map(msg => 
                msg.id === aiMessageId ? { ...msg, responseTime: totalTime } : msg
              ));
              continue;
            }
            
            try {
              const data = JSON.parse(dataStr);
              if (data.text) {
                setMessages(prev => prev.map(msg => 
                  msg.id === aiMessageId ? { ...msg, content: msg.content + data.text } : msg
                ));
              } else if (data.sources) {
                setMessages(prev => prev.map(msg => 
                  msg.id === aiMessageId ? { ...msg, sources: data.sources } : msg
                ));
              }
            } catch (e) {
              console.error("Error parsing JSON chunk", e, dataStr);
            }
          }
        }
      }

    } catch (error) {
      console.error("Failed to ask question", error);
      setMessages(prev => [...prev, { id: Date.now(), role: 'ai', content: 'Sorry, an error occurred while processing your question.' }]);
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 h-[calc(100vh-80px)] flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Document Chat</h1>
        <button onClick={() => navigate('/')} className="text-gray-600 hover:text-black">
          &larr; Back to Dashboard
        </button>
      </div>

      <div className="flex-1 bg-white rounded-lg shadow-md flex flex-col overflow-hidden">
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 bg-gray-50">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-10">
              Ask a question about your document to get started!
            </div>
          )}
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[90%] md:max-w-[75%] rounded-lg p-3 md:p-4 shadow-sm ${
                msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-white border text-gray-800 rounded-bl-none'
              }`}>
                {msg.role === 'ai' ? (
                  <div className="prose prose-sm max-w-none text-gray-800 break-words overflow-hidden relative pb-4">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                    {msg.responseTime && (
                      <span className="absolute bottom-[-5px] right-0 text-[10px] text-gray-400">
                        ⏱ {msg.responseTime}s
                      </span>
                    )}
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border text-gray-800 rounded-lg rounded-bl-none p-3 shadow-sm">
                <span className="animate-pulse">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-3 md:p-4 bg-white border-t">
          <form onSubmit={handleAsk} className="flex gap-2 md:gap-4">
            <input 
              type="text" 
              value={question} 
              onChange={e => setQuestion(e.target.value)}
              placeholder="Ask a question..." 
              className="flex-1 px-4 py-2 md:py-3 border rounded-full focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-sm md:text-base"
              disabled={loading}
            />
            <button 
              type="submit" 
              disabled={loading || !question.trim()}
              className="bg-blue-600 text-white px-4 md:px-8 py-2 md:py-3 rounded-full hover:bg-blue-700 disabled:bg-blue-300 transition-colors text-sm md:text-base flex-shrink-0"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Chat;
