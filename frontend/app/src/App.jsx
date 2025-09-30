import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Login from './components/Login';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
    const [user, setUser] = useState(null);
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [activeMode, setActiveMode] = useState('literature');
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [chatSessions, setChatSessions] = useState([]);
    const [currentSessionId, setCurrentSessionId] = useState(null);
    const [error, setError] = useState(null);
    const [isOnline, setIsOnline] = useState(navigator.onLine);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        // Check for existing user session
        const token = localStorage.getItem('token');
        const userData = localStorage.getItem('user');
        
        if (token && userData) {
            setUser(JSON.parse(userData));
            loadChatSessions();
        }

        // Monitor online/offline status
        const handleOnline = () => setIsOnline(true);
        const handleOffline = () => setIsOnline(false);
        
        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);
        
        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, []);

    useEffect(() => {
        if (user) {
            // Initialize with welcome message
            setMessages([
                {
                    id: 1,
                    role: 'assistant',
                    content: `👋 Welcome back, ${user.full_name || user.username}!\n\nI can help you:\n🔍 Search Literature - Find relevant research papers and clinical trials\n🧬 Generate Hypotheses - Create AI-powered research hypotheses\n📥 Download Data - Get compound and protein structure data\n📊 Generate Graphs - Visualize relationships and networks\n\nWhat would you like to explore today?`,
                    timestamp: new Date().toISOString()
                }
            ]);
        }
    }, [user]);

    const loadChatSessions = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await axios.get(`${API_URL}/api/chat/sessions`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setChatSessions(response.data);
        } catch (error) {
            console.error('Error loading chat sessions:', error);
            setError('Failed to load chat history. Please try again.');
        }
    };

    const createNewChatSession = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await axios.post(`${API_URL}/api/chat/sessions`, {
                title: 'New Chat'
            }, {
                headers: { Authorization: `Bearer ${token}` }
            });
            
            setCurrentSessionId(response.data.id);
            setChatSessions(prev => [response.data, ...prev]);
            setMessages([]);
            setError(null);
        } catch (error) {
            console.error('Error creating chat session:', error);
            setError('Failed to create new chat session. Please try again.');
        }
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!inputValue.trim() || isLoading || !user || !isOnline) return;

        const userMessage = {
            id: Date.now(),
            role: 'user',
            content: inputValue,
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);
        setError(null);

        try {
            let response;
            if (activeMode === 'literature') {
                response = await axios.post(`${API_URL}/api/search`, {
                    query: inputValue,
                    mode: 'literature'
                });
            } else if (activeMode === 'hypothesis') {
                response = await axios.post(`${API_URL}/api/hypothesis`, {
                    text: inputValue
                });
            } else if (activeMode === 'download') {
                response = await axios.post(`${API_URL}/api/download`, {
                    compound_name: inputValue
                });
            } else if (activeMode === 'graph') {
                response = await axios.post(`${API_URL}/api/graph`, {
                    query: inputValue,
                    graph_type: 'network'
                });
            }

            const assistantMessage = {
                id: Date.now() + 1,
                role: 'assistant',
                content: formatResponse(response.data, activeMode),
                timestamp: new Date().toISOString(),
                mode: activeMode
            };

            setMessages(prev => [...prev, assistantMessage]);

            // Save messages to database if we have a session
            if (currentSessionId) {
                const token = localStorage.getItem('token');
                await axios.post(`${API_URL}/api/chat/sessions/${currentSessionId}/messages`, {
                    content: inputValue,
                    mode: activeMode
                }, {
                    headers: { Authorization: `Bearer ${token}` }
                });
            }
        } catch (error) {
            console.error('Error:', error);
            const errorMessage = {
                id: Date.now() + 1,
                role: 'assistant',
                content: error.response?.status === 401 
                    ? 'Your session has expired. Please log in again.'
                    : error.response?.status === 429
                    ? 'Too many requests. Please wait a moment and try again.'
                    : 'Sorry, I encountered an error processing your request. Please try again.',
                timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, errorMessage]);
            setError('Failed to process your request. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
        setMessages([]);
        setChatSessions([]);
        setCurrentSessionId(null);
        setError(null);
    };

    const clearError = () => {
        setError(null);
    };

    const formatResponse = (data, mode) => {
        if (mode === 'literature') {
            let content = `📚 Literature Search Results for "${data.query}"\n\n`;
            content += `AI Summary: ${data.rag_summary}\n\n`;
            
            if (data.pubmed_articles && data.pubmed_articles.length > 0) {
                content += `PubMed Articles (${data.pubmed_articles.length}):\n`;
                data.pubmed_articles.forEach((article, index) => {
                    content += `${index + 1}. ${article.title}\n`;
                    content += `   ${article.abstract.substring(0, 200)}...\n`;
                    if (article.url) {
                        content += `   🔗 View Article: ${article.url}\n`;
                    }
                    content += `\n`;
                });
            }
            
            if (data.clinical_trials && data.clinical_trials.length > 0) {
                content += `Clinical Trials (${data.clinical_trials.length}):\n`;
                data.clinical_trials.forEach((trial, index) => {
                    content += `${index + 1}. ${trial.title}\n`;
                    content += `   Status: ${trial.status}\n`;
                    if (trial.url) {
                        content += `   🔗 View Trial: ${trial.url}\n`;
                    }
                    content += `\n`;
                });
            }
            
            content += `\n${data.sponsor_tech}`;
            return content;
        } else if (mode === 'hypothesis') {
            let content = `🧬 AI-Generated Hypothesis\n\n`;
            content += `Input: ${data.input}\n\n`;
            content += `Hypothesis: ${data.hypothesis}\n\n`;
            content += `Plausibility Score: ${(data.plausibility_score * 100).toFixed(1)}%\n`;
            content += `Confidence: ${data.confidence}\n\n`;
            
            if (data.citations && data.citations.length > 0) {
                content += `Supporting Literature:\n`;
                data.citations.forEach((citation, index) => {
                    content += `${index + 1}. ${citation.title}\n`;
                    if (citation.url) {
                        content += `   🔗 View: ${citation.url}\n`;
                    }
                });
                content += `\n`;
            }
            
            content += `${data.sponsor_tech}`;
            return content;
        } else if (mode === 'download') {
            let content = `📥 Download Data for "${data.compound_name}"\n\n`;
            content += `PubChem Data:\n`;
            content += `- Name: ${data.pubchem_data.name}\n`;
            content += `- Molecular Formula: ${data.pubchem_data.molecular_formula}\n`;
            content += `- Molecular Weight: ${data.pubchem_data.molecular_weight}\n\n`;
            
            content += `Protein Structure:\n`;
            content += `- PDB ID: ${data.protein_structure.pdb_id}\n`;
            content += `- Method: ${data.protein_structure.method}\n`;
            content += `- Resolution: ${data.protein_structure.resolution} Å\n\n`;
            
            content += `Download Links:\n`;
            Object.entries(data.download_links).forEach(([key, url]) => {
                const label = key.replace(/_/g, ' ').toUpperCase();
                content += `- 🔗 ${label}: ${url}\n`;
            });
            
            content += `\n${data.sponsor_tech}`;
            return content;
        } else if (mode === 'graph') {
            let content = `📊 Graph Visualization for "${data.query}"\n\n`;
            content += `Graph Type: ${data.graph_type}\n\n`;
            
            content += `Nodes (${data.nodes.length}):\n`;
            data.nodes.forEach((node, index) => {
                content += `${index + 1}. ${node.label} (${node.type})\n`;
            });
            content += `\n`;
            
            content += `Connections (${data.edges.length}):\n`;
            data.edges.forEach((edge, index) => {
                const sourceNode = data.nodes.find(n => n.id === edge.source);
                const targetNode = data.nodes.find(n => n.id === edge.target);
                content += `${index + 1}. ${sourceNode?.label} → ${targetNode?.label} (${edge.type})\n`;
            });
            content += `\n`;
            
            content += `Download Links:\n`;
            Object.entries(data.download_links).forEach(([key, url]) => {
                const label = key.replace(/_/g, ' ').toUpperCase();
                content += `- 🔗 ${label}: ${url}\n`;
            });
            
            content += `\n${data.sponsor_tech}`;
            return content;
        }
        return JSON.stringify(data, null, 2);
    };

    const handleModeChange = (mode) => {
        setActiveMode(mode);
        setInputValue('');
    };

    const getModeIcon = (mode) => {
        switch (mode) {
            case 'literature': return '🟢';
            case 'hypothesis': return '🔵';
            case 'download': return '🟠';
            case 'graph': return '🟣';
            default: return '⚪';
        }
    };

    const getModeLabel = (mode) => {
        switch (mode) {
            case 'literature': return 'Search Literature';
            case 'hypothesis': return 'Generate Hypothesis';
            case 'download': return 'Download Data';
            case 'graph': return 'Generate Graph';
            default: return 'Chat';
        }
    };

    // Function to detect and make URLs clickable
    const linkifyText = (text) => {
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        return text.replace(urlRegex, (url) => {
            return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:text-blue-300 underline">${url}</a>`;
        });
    };

    // Function to render message content with clickable links
    const renderMessageContent = (content) => {
        const linkifiedContent = linkifyText(content);
        return <div dangerouslySetInnerHTML={{ __html: linkifiedContent }} />;
    };

    // Show login screen if user is not authenticated
    if (!user) {
        return <Login onLogin={setUser} />;
    }

    return (
        <div className="min-h-screen bg-gray-900 flex">
            {/* Sidebar */}
            <div className={`${sidebarOpen ? 'w-64' : 'w-0'} transition-all duration-300 bg-gray-800 shadow-xl overflow-hidden border-r border-gray-700`}>
                <div className="p-4">
                    <div className="flex items-center mb-6">
                        <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3">
                            <span className="text-white font-bold text-sm">C</span>
                        </div>
                        <h2 className="text-lg font-semibold text-white">Clintra</h2>
                    </div>
                        <nav className="space-y-1">
                            <button
                                onClick={createNewChatSession}
                                className="w-full text-left p-3 rounded-lg hover:bg-gray-700 flex items-center text-gray-300 hover:text-white transition-colors"
                            >
                                <span className="mr-3 text-lg">💬</span>
                                New Chat
                            </button>
                            
                            <div className="border-t border-gray-700 my-4"></div>
                            
                            <div className="text-xs text-gray-400 uppercase tracking-wide mb-2 px-3">
                                Recent Chats
                            </div>
                            
                            {chatSessions.slice(0, 5).map((session) => (
                                <button
                                    key={session.id}
                                    onClick={() => {
                                        setCurrentSessionId(session.id);
                                        setSidebarOpen(false);
                                    }}
                                    className={`w-full text-left p-3 rounded-lg hover:bg-gray-700 flex items-center text-gray-300 hover:text-white transition-colors ${
                                        currentSessionId === session.id ? 'bg-gray-700' : ''
                                    }`}
                                >
                                    <span className="mr-3 text-lg">💭</span>
                                    <div className="flex-1 min-w-0">
                                        <div className="truncate text-sm">{session.title}</div>
                                        <div className="text-xs text-gray-500">{session.message_count} messages</div>
                                    </div>
                                </button>
                            ))}
                            
                            <div className="border-t border-gray-700 my-4"></div>
                            
                            <button
                                onClick={handleLogout}
                                className="w-full text-left p-3 rounded-lg hover:bg-gray-700 flex items-center text-gray-300 hover:text-white transition-colors"
                            >
                                <span className="mr-3 text-lg">🚪</span>
                                Logout
                            </button>
                        </nav>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col">
                {/* Header */}
                <header className="bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between">
                    <button
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className="p-2 rounded-lg hover:bg-gray-700 text-gray-300 hover:text-white transition-colors"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    </button>
                        <div className="flex items-center">
                            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3">
                                <span className="text-white font-bold text-sm">C</span>
                            </div>
                            <h1 className="text-xl font-semibold text-white">Clintra</h1>
                        </div>
                        
                        <div className="flex items-center space-x-4">
                            <div className="flex items-center space-x-2">
                                <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`}></div>
                                <span className="text-xs text-gray-400">
                                    {isOnline ? 'Online' : 'Offline'}
                                </span>
                            </div>
                            <div className="text-sm text-gray-300">
                                Welcome, {user.full_name || user.username}
                            </div>
                            <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
                                <span className="text-white font-bold text-sm">
                                    {(user.full_name || user.username).charAt(0).toUpperCase()}
                                </span>
                            </div>
                        </div>
                    <div className="w-8"></div>
            </header>

                {/* Error Banner */}
                {error && (
                    <div className="bg-red-900/50 border-l-4 border-red-500 p-4 mx-4 mt-4 rounded-lg">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center">
                                <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                </svg>
                                <span className="text-red-200 text-sm">{error}</span>
                            </div>
                            <button
                                onClick={clearError}
                                className="text-red-400 hover:text-red-300 transition-colors"
                            >
                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                                </svg>
                        </button>
                        </div>
                    </div>
                )}

                {/* Chat Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-gray-900">
                    {messages.map((message) => (
                        <div
                            key={message.id}
                            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div className={`flex max-w-4xl ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                                {/* Avatar */}
                                <div className={`flex-shrink-0 ${message.role === 'user' ? 'ml-3' : 'mr-3'}`}>
                                    {message.role === 'user' ? (
                                        <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center">
                                            <span className="text-white font-bold text-sm">U</span>
                                        </div>
                                    ) : (
                                        <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                                            <span className="text-white font-bold text-sm">C</span>
                                        </div>
                                    )}
                                </div>
                                
                                {/* Message Content */}
                                <div
                                    className={`p-4 rounded-2xl ${
                                        message.role === 'user'
                                            ? 'bg-gray-700 text-white'
                                            : 'bg-gray-800 text-gray-100 border border-gray-700'
                                    }`}
                                >
                                    <div className="message-content">{renderMessageContent(message.content)}</div>
                                    {message.mode && (
                                        <div className="mt-2 text-xs text-gray-400">
                                            Mode: {getModeLabel(message.mode)}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex justify-start">
                            <div className="flex">
                                <div className="flex-shrink-0 mr-3">
                                    <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                                        <span className="text-white font-bold text-sm">C</span>
                                    </div>
                                </div>
                                <div className="bg-gray-800 text-gray-100 p-4 rounded-2xl border border-gray-700">
                                    <div className="flex items-center space-x-2">
                                        <div className="flex space-x-1">
                                            <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                                            <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                                            <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                                        </div>
                                        <span className="text-sm font-medium">Clintra is thinking...</span>
                                    </div>
                                </div>
                            </div>
                            </div>
                        )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="bg-gray-800 border-t border-gray-700 p-4">
                    {/* Quick Action Buttons */}
                    <div className="flex space-x-2 mb-4">
                        <button
                            onClick={() => handleModeChange('literature')}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                                activeMode === 'literature'
                                    ? 'bg-green-600 text-white shadow-lg'
                                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white'
                            }`}
                        >
                            🔍 Search Literature
                        </button>
                        <button
                            onClick={() => handleModeChange('hypothesis')}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                                activeMode === 'hypothesis'
                                    ? 'bg-blue-600 text-white shadow-lg'
                                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white'
                            }`}
                        >
                            🧬 Generate Hypothesis
                        </button>
                        <button
                            onClick={() => handleModeChange('download')}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                                activeMode === 'download'
                                    ? 'bg-amber-600 text-white shadow-lg'
                                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white'
                            }`}
                        >
                            📥 Download Data
                        </button>
                        <button
                            onClick={() => handleModeChange('graph')}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                                activeMode === 'graph'
                                    ? 'bg-purple-600 text-white shadow-lg'
                                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white'
                            }`}
                        >
                            📊 Generate Graph
                        </button>
                    </div>

                    {/* Search Input */}
                    <form onSubmit={handleSendMessage} className="flex space-x-3">
                        <div className="flex-1 relative">
                            <input
                                type="text"
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                placeholder={!isOnline 
                                    ? "You're offline. Please check your connection."
                                    : `Ask me about a disease, protein, or drug... (${getModeLabel(activeMode)} mode)`
                                }
                                className="w-full p-4 bg-gray-700 text-white placeholder-gray-400 rounded-xl border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all disabled:opacity-50"
                                disabled={isLoading || !isOnline}
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={isLoading || !inputValue.trim() || !isOnline}
                            className="px-6 py-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                            </svg>
                            </button>
                        </form>
                </div>
            </div>
        </div>
    );
}

export default App;