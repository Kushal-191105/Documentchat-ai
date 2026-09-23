import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

const Dashboard = () => {
  const [documents, setDocuments] = useState([]);
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDocuments();
    // Auto-refresh every 3 seconds to update document status
    const interval = setInterval(() => {
      fetchDocuments();
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await api.get('documents/');
      setDocuments(res.data);
    } catch (error) {
      if (error.response?.status === 401) {
        navigate('/login');
      }
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file || !title) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);

    setLoading(true);
    try {
      await api.post('documents/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setFile(null);
      setTitle('');
      fetchDocuments();
    } catch (error) {
      console.error("Upload failed", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`documents/${id}/`);
      fetchDocuments();
    } catch (error) {
      console.error("Delete failed", error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        
        {/* Upload Form */}
        <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 mb-8">
          <h2 className="text-xl font-bold mb-6 text-gray-800">Upload New Document</h2>
          <form onSubmit={handleUpload} className="flex flex-col md:flex-row gap-6 items-end">
            <div className="flex-1 w-full">
              <label className="block text-gray-700 font-medium text-sm mb-2">Document Title</label>
              <input type="text" value={title} onChange={e => setTitle(e.target.value)}
                     placeholder="e.g., Q3 Financial Report"
                     className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" required />
            </div>
          <div className="flex-1 w-full">
            <label className="block text-gray-700 font-medium text-sm mb-2">PDF File</label>
            <input type="file" accept=".pdf" onChange={e => setFile(e.target.files[0])}
                   className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-50 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer" required />
          </div>
          <button type="submit" disabled={loading} 
                  className="w-full md:w-auto bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 disabled:bg-blue-300 font-medium transition-colors shadow-sm">
            {loading ? 'Uploading...' : 'Upload Document'}
          </button>
        </form>
      </div>

      {/* Document List */}
      <h2 className="text-xl font-bold mb-6 text-gray-800">Your Documents</h2>
      {documents.length === 0 && (
        <div className="text-center py-12 bg-white rounded-xl border border-dashed border-gray-300">
          <p className="text-gray-500">You haven't uploaded any documents yet.</p>
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {documents.map(doc => (
          <div key={doc.id} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow relative overflow-hidden">
            {/* Status indicator bar at top */}
            <div className={`absolute top-0 left-0 w-full h-1 ${
              doc.status === 'completed' ? 'bg-green-500' : 
              doc.status === 'error' ? 'bg-red-500' : 'bg-yellow-500 animate-pulse'
            }`} />
            
            <h3 className="text-lg font-bold mb-3 text-gray-800 line-clamp-1" title={doc.title}>{doc.title}</h3>
            
            <div className="flex items-center justify-between mb-6">
              <span className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1 ${
                doc.status === 'completed' ? 'bg-green-50 text-green-700 border border-green-200' : 
                doc.status === 'error' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-yellow-50 text-yellow-700 border border-yellow-200'
              }`}>
                {doc.status === 'processing' && (
                  <svg className="animate-spin h-3 w-3 mr-1" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
                {doc.status.toUpperCase()}
              </span>
              {doc.processing_time && (
                <span className="text-xs text-gray-400">Processed in {doc.processing_time}s</span>
              )}
            </div>
            
            <div className="flex justify-between items-center pt-4 border-t border-gray-100">
              <button onClick={() => navigate(`/chat/${doc.id}`)} disabled={doc.status !== 'completed'}
                      className={`font-medium ${doc.status === 'completed' ? 'text-blue-600 hover:text-blue-800' : 'text-gray-400 cursor-not-allowed'}`}>
                Chat &rarr;
              </button>
              <button onClick={() => handleDelete(doc.id)} className="text-gray-400 hover:text-red-600 transition-colors" title="Delete Document">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
    </div>
  );
};

export default Dashboard;
