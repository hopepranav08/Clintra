import React, { useState, useEffect, useRef } from 'react';
import ClintraLogo from './ClintraLogo';

const ChatPage = ({ user, messages, activeMode, onModeChange, onBack, onLogout, onNavigate, onSendMessage, inputValue, setInputValue, isLoading }) => {
    const [showProfileMenu, setShowProfileMenu] = useState(false);
    const [showSearch, setShowSearch] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const messagesEndRef = useRef(null);
    const messagesContainerRef = useRef(null);
    
    // Search functionality
    const handleSearch = (query) => {
        if (!query.trim()) {
            setSearchResults([]);
            return;
        }
        
        const results = messages.filter(message => 
            message.content.toLowerCase().includes(query.toLowerCase()) ||
            message.role.toLowerCase().includes(query.toLowerCase())
        );
        setSearchResults(results);
    };
    
    const handleSearchChange = (e) => {
        const query = e.target.value;
        setSearchQuery(query);
        handleSearch(query);
    };
    
    // Enhanced content formatting for AI responses
    const formatContent = (content) => {
        let formatted = content;
        
        // Convert markdown links to HTML with theme colors
        formatted = formatted.replace(/\*\*\[([^\]]+)\]\(([^)]+)\)\*\*/g, (match, text, url) => {
            return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-clintra-teal hover:text-clintra-cyan underline font-medium transition-colors duration-200 hover:bg-clintra-teal/10 px-1 py-0.5 rounded">${text}</a>`;
        });
        formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, url) => {
            return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-clintra-teal hover:text-clintra-cyan underline font-medium transition-colors duration-200 hover:bg-clintra-teal/10 px-1 py-0.5 rounded">${text}</a>`;
        });
        
        // Format PDB IDs as clickable links with special styling
        formatted = formatted.replace(/\b([A-Z0-9]{4})\b/g, (match, pdbId) => {
            if (pdbId.length === 4 && /^[A-Z0-9]+$/.test(pdbId)) {
                return `<a href="https://www.rcsb.org/structure/${pdbId}" target="_blank" rel="noopener noreferrer" class="text-clintra-gold hover:text-clintra-gold/80 font-mono font-bold bg-clintra-gold/10 px-2 py-1 rounded-lg border border-clintra-gold/20 transition-all hover:bg-clintra-gold/20 hover:border-clintra-gold/40 hover:scale-105">${pdbId}</a>`;
            }
            return match;
        });
        
        // Format bold text with better styling
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-white bg-white/5 px-1 py-0.5 rounded">$1</strong>');
        
        // Format headings with theme colors
        formatted = formatted.replace(/^# (.*$)/gm, '<h1 class="text-xl font-bold text-clintra-teal mb-3 mt-6 first:mt-0">$1</h1>');
        formatted = formatted.replace(/^## (.*$)/gm, '<h2 class="text-lg font-semibold text-clintra-cyan mb-2 mt-4">$1</h2>');
        formatted = formatted.replace(/^### (.*$)/gm, '<h3 class="text-base font-medium text-white mb-2 mt-3">$1</h3>');
        
        // Format bullet points with theme colors
        formatted = formatted.replace(/^(\s*)[•\-*]\s+(.*)$/gm, '<div class="flex items-start my-2"><span class="text-clintra-teal mr-3 mt-1 text-lg">•</span><span class="flex-1">$2</span></div>');
        
        // Format numbered lists
        formatted = formatted.replace(/^(\s*)(\d+)\.\s+(.*)$/gm, '<div class="flex items-start my-2"><span class="text-clintra-gold mr-3 mt-1 font-bold min-w-[1.5rem]">$2.</span><span class="flex-1">$3</span></div>');
        
        // Format code blocks with theme styling
        formatted = formatted.replace(/`([^`]+)`/g, '<code class="bg-clintra-navy-lighter text-clintra-teal font-mono text-xs px-2 py-1 rounded border border-clintra-teal/20">$1</code>');
        
        // Format paragraphs with proper spacing
        formatted = formatted.replace(/\n\n/g, '</p><p class="my-3">');
        formatted = '<p class="my-3">' + formatted + '</p>';
        
        // Clean up empty paragraphs
        formatted = formatted.replace(/<p class="my-3"><\/p>/g, '');
        
        return formatted;
    };
    
    // Complete theme system per mode
    const getModeTheme = () => {
        switch(activeMode) {
            case 'literature':
                return {
                    title: 'Literature Search',
                    description: 'Search and analyze research papers from PubMed, Clinical Trials, and biomedical databases',
                    icon: (
                        <svg className="w-20 h-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    ),
                    // Colors
                    textColor: 'text-clintra-cyan',
                    borderColor: 'border-clintra-cyan/30',
                    hoverBorder: 'hover:border-clintra-cyan',
                    bgGradient: 'from-clintra-teal to-clintra-cyan',
                    navColor: 'clintra-cyan',
                    logoGradient: 'from-clintra-teal to-clintra-cyan',
                    glow: 'glow-literature',
                    bannerBg: 'bg-clintra-teal/5'
                };
            case 'hypothesis':
                return {
                    title: 'Hypothesis Generation',
                    description: 'Generate AI-powered research hypotheses with supporting evidence and citations',
                    icon: (
                        <svg className="w-20 h-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                    ),
                    // Colors
                    textColor: 'text-clintra-purple',
                    borderColor: 'border-clintra-purple/30',
                    hoverBorder: 'hover:border-clintra-purple',
                    bgGradient: 'from-clintra-purple-dark to-clintra-purple',
                    navColor: 'clintra-purple',
                    logoGradient: 'from-clintra-purple-dark to-clintra-purple',
                    glow: 'glow-hypothesis',
                    bannerBg: 'bg-clintra-purple/5'
                };
            case 'download':
                return {
                    title: 'Download Data',
                    description: 'Access compound and protein structure data from PubChem and PDB databases',
                    icon: (
                        <svg className="w-20 h-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                        </svg>
                    ),
                    // Colors
                    textColor: 'text-clintra-gold',
                    borderColor: 'border-clintra-gold/30',
                    hoverBorder: 'hover:border-clintra-gold',
                    bgGradient: 'from-clintra-gold-dark to-clintra-gold',
                    navColor: 'clintra-gold',
                    logoGradient: 'from-clintra-gold-dark to-clintra-gold',
                    glow: 'glow-download',
                    bannerBg: 'bg-clintra-gold/5'
                };
            default:
                return {
                    title: 'Literature Search',
                    description: 'Search research papers',
                    icon: (
                        <svg className="w-20 h-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    ),
                    textColor: 'text-clintra-cyan',
                    borderColor: 'border-clintra-cyan/30',
                    hoverBorder: 'hover:border-clintra-cyan',
                    bgGradient: 'from-clintra-teal to-clintra-cyan',
                    navColor: 'clintra-cyan',
                    logoGradient: 'from-clintra-teal to-clintra-cyan',
                    glow: 'glow-literature',
                    bannerBg: 'bg-clintra-teal/5'
                };
        }
    };

    const theme = getModeTheme();

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages, isLoading]);

    // Close profile menu when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (showProfileMenu && !event.target.closest('.profile-menu')) {
                setShowProfileMenu(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [showProfileMenu]);

    return (
        <div className="h-screen flex flex-col bg-clintra-navy-darker">
            {/* 🎨 ENHANCED NAVBAR - Ultra Dark Theme */}
            <nav className={`bg-clintra-navy-dark border-b ${theme.borderColor} px-6 py-3 transition-all duration-500 backdrop-blur-sm`}>
                <div className="flex items-center justify-between">
                    {/* Left: Enhanced Logo - Clickable to go Home */}
                    <button 
                        onClick={onBack}
                        className="flex items-center space-x-3 hover:opacity-90 transition-all duration-300 group"
                    >
                        <div className="group-hover:scale-110 transition-transform duration-300">
                            <ClintraLogo size="lg" />
                        </div>
                        <h1 className={`text-xl font-black ${theme.textColor} transition-all duration-500 group-hover:scale-105`}>CLINTRA</h1>
                    </button>
                    
                    {/* Right: Enhanced Online Status, Welcome + Username */}
                    <div className="flex items-center space-x-8">
                        {/* Enhanced Online Status */}
                        <div className="flex items-center space-x-2">
                            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-400/50"></div>
                            <span className="text-white/80 text-sm font-medium">Online</span>
                        </div>
                        
                        {/* Enhanced Welcome + Username */}
                        <div className="flex items-center space-x-2">
                            <span className="text-white/70 text-sm font-medium">Welcome,</span>
                            <span className="text-white font-bold text-base">{user?.username || 'User'}</span>
                        </div>
                        
                        {/* Enhanced Profile Button */}
                        <div className="relative profile-menu">
                            <button 
                                onClick={() => setShowProfileMenu(!showProfileMenu)}
                                className={`w-10 h-10 bg-gradient-to-br ${theme.logoGradient} rounded-2xl flex items-center justify-center ${theme.glow} hover:shadow-xl hover:scale-110 transition-all duration-300 cursor-pointer group`}
                            >
                                <span className="text-white font-bold text-sm group-hover:scale-110 transition-transform duration-300">{user?.username?.charAt(0).toUpperCase() || 'U'}</span>
                            </button>
                            
                            {/* Enhanced Dropdown Menu - Fixed positioning */}
                            {showProfileMenu && (
                                <div className="absolute right-0 top-full mt-2 w-64 bg-clintra-navy-dark border border-clintra-teal/30 rounded-xl shadow-2xl py-2 z-[9999] backdrop-blur-xl slide-in-right">
                                    <button 
                                        onClick={() => setShowProfileMenu(false)}
                                        className="w-full text-left px-4 py-3 hover:bg-clintra-teal/10 text-white transition-all duration-300 flex items-center space-x-3 group"
                                    >
                                        <svg className="w-4 h-4 text-clintra-cyan/70 group-hover:text-clintra-cyan transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                        </svg>
                                        <span className="font-medium text-sm">Account Settings</span>
                                    </button>
                                    
                                    <button 
                                        onClick={() => setShowProfileMenu(false)}
                                        className="w-full text-left px-4 py-3 hover:bg-clintra-teal/10 text-white transition-all duration-300 flex items-center space-x-3 group"
                                    >
                                        <svg className="w-4 h-4 text-clintra-cyan/70 group-hover:text-clintra-cyan transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                                        </svg>
                                        <span className="font-medium text-sm">Import / Export Chat</span>
                                    </button>
                                    
                                    <button 
                                        onClick={() => {
                                            setShowSearch(!showSearch);
                                            setShowProfileMenu(false);
                                        }}
                                        className="w-full text-left px-4 py-3 hover:bg-clintra-teal/10 text-white transition-all duration-300 flex items-center space-x-3 group"
                                    >
                                        <svg className="w-4 h-4 text-clintra-cyan/70 group-hover:text-clintra-cyan transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                        </svg>
                                        <span className="font-medium text-sm">Search Messages</span>
                                    </button>
                                    
                                    <div className="border-t border-clintra-teal/20 my-2"></div>
                                    
                                    <button 
                                        onClick={() => {
                                            if (onLogout) onLogout();
                                            setShowProfileMenu(false);
                                        }}
                                        className="w-full text-left px-4 py-3 hover:bg-red-500/10 text-red-400 transition-all duration-300 flex items-center space-x-3 group"
                                    >
                                        <svg className="w-4 h-4 text-red-400/70 group-hover:text-red-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                                        </svg>
                                        <span className="font-medium text-sm">Logout</span>
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </nav>

            {/* Enhanced Search Interface */}
            {showSearch && (
                <div className="bg-clintra-navy-dark border-b border-clintra-teal/30 p-6 backdrop-blur-sm slide-in-left">
                    <div className="max-w-6xl mx-auto">
                        <div className="flex items-center space-x-6">
                            <div className="flex-1 relative">
                                <input
                                    type="text"
                                    placeholder="Search messages..."
                                    value={searchQuery}
                                    onChange={handleSearchChange}
                                    className="w-full bg-clintra-navy border border-clintra-teal/40 rounded-2xl px-6 py-4 text-white placeholder-clintra-teal/70 focus:outline-none focus:border-clintra-teal-bright focus:ring-2 focus:ring-clintra-teal/30 text-lg font-medium transition-all duration-300"
                                />
                                <svg className="absolute right-4 top-4 w-6 h-6 text-clintra-teal/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            </div>
                            <button
                                onClick={() => setShowSearch(false)}
                                className="text-clintra-teal hover:text-clintra-cyan-bright transition-colors hover:scale-110 transform duration-300"
                            >
                                <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                        
                        {/* Enhanced Search Results */}
                        {searchResults.length > 0 && (
                            <div className="mt-6 max-h-80 overflow-y-auto">
                                <h3 className="text-clintra-cyan-bright font-bold text-lg mb-4">Search Results ({searchResults.length})</h3>
                                <div className="space-y-3">
                                    {searchResults.map((message, index) => (
                                        <div key={index} className="bg-clintra-navy border border-clintra-teal/30 rounded-2xl p-4 hover:border-clintra-teal-bright transition-all duration-300 group">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className={`text-sm font-bold px-3 py-1 rounded-full ${
                                                    message.role === 'user' 
                                                        ? 'bg-clintra-purple/20 text-clintra-purple-bright' 
                                                        : 'bg-clintra-teal/20 text-clintra-teal-bright'
                                                }`}>
                                                    {message.role === 'user' ? 'You' : 'Clintra'}
                                                </span>
                                                <span className="text-sm text-clintra-teal/70 font-medium">
                                                    {new Date(message.timestamp || Date.now()).toLocaleTimeString()}
                                                </span>
                                            </div>
                                            <div className="text-base text-white/90 leading-relaxed">
                                                {message.content.substring(0, 300)}{message.content.length > 300 ? '...' : ''}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                        
                        {searchQuery && searchResults.length === 0 && (
                            <div className="mt-6 text-center text-clintra-teal/70 text-lg font-medium">
                                No messages found matching "{searchQuery}"
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* 🎨 3-SECTION LAYOUT - MUCH BIGGER middle section for chat */}
            <div className="flex-1 grid grid-cols-[180px_1fr_200px] overflow-hidden">
                
                {/* ═══════════════════════════════════════ */}
                {/* LEFT SECTION: Enhanced Chat History */}
                {/* ═══════════════════════════════════════ */}
                <div className={`bg-clintra-navy-darker border-r ${theme.borderColor} p-6 overflow-y-auto transition-all duration-500`}>
                    <h2 className="text-white font-bold mb-6 text-lg">Chat Sessions</h2>
                    
                    {/* Professional New Chat Button */}
                    <button 
                        onClick={async () => {
                            // Save current chat to history if it has messages
                            if (window.saveCurrentChatToHistory && window.messages && window.messages.length > 0) {
                                try {
                                    await window.saveCurrentChatToHistory();
                                    console.log('✅ Current chat saved to history');
                                } catch (error) {
                                    console.error('Error saving current chat:', error);
                                }
                            }
                            // Create new chat session
                            if (window.createNewChatSession) {
                                try {
                                    await window.createNewChatSession();
                                    console.log('✅ New chat session created');
                                } catch (error) {
                                    console.error('Error creating new chat:', error);
                                }
                            }
                            // Clear messages and show description
                            if (window.clearMessages) {
                                window.clearMessages();
                            }
                        }}
                        className="w-full bg-clintra-navy border border-clintra-teal/30 hover:border-clintra-teal text-white p-3 rounded-xl mb-6 transition-all duration-300 hover:bg-clintra-teal/10 font-medium text-sm group"
                    >
                        <span className="flex items-center justify-center space-x-2">
                            <svg className="w-4 h-4 text-clintra-cyan group-hover:text-clintra-cyan-bright transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                            </svg>
                            <span>New Chat</span>
                        </span>
                    </button>
                    
                    {/* Enhanced History */}
                    <div className="space-y-4">
                        <h3 className="text-white/80 text-sm font-bold mb-4">RECENT CHATS</h3>
                        <div className="space-y-3">
                            {(window.chatSessions || []).map((session, idx) => (
                                <div 
                                    key={session.id || idx}
                                    onClick={() => {
                                        console.log('🖱️ Clicked on session:', session.id, session.title);
                                        if (window.switchToSession) {
                                            console.log('🔄 Calling switchToSession...');
                                            window.switchToSession(session.id);
                                        } else {
                                            console.error('❌ switchToSession not available');
                                        }
                                    }}
                                    className="bg-clintra-navy border border-clintra-teal/30 hover:border-clintra-teal-bright p-4 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-105 hover:shadow-xl group"
                                >
                                    <div className="text-white text-sm font-semibold truncate group-hover:text-clintra-cyan-bright transition-colors">{session.title || `Chat ${idx + 1}`}</div>
                                    <div className="text-clintra-teal/70 text-xs mt-2 font-medium">
                                        {new Date(session.created_at || Date.now()).toLocaleDateString()}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* ═══════════════════════════════════════ */}
                {/* MIDDLE SECTION: Chat Messages */}
                {/* ═══════════════════════════════════════ */}
                <div className="flex flex-col bg-clintra-navy">
                    {/* Mode Info - Only shows when NO messages (first time) */}
                    {messages.length === 0 && (
                        <div className="p-10 text-left transition-all duration-700">
                            <div className="max-w-4xl">
                                {/* Animated Icon - Clean SVG, No Background */}
                                <div className={`mb-5 float inline-block ${theme.textColor}`}>
                                    <div className={`${theme.glow} p-2 rounded-xl`}>
                                        {theme.icon}
                                    </div>
                                </div>
                                
                                {/* Animated Title */}
                                <h2 className={`${theme.textColor} text-3xl font-bold mb-3 slide-in-left tracking-tight`}>
                                    {theme.title}
                                </h2>
                                
                                {/* Description - Shows only first time */}
                                <p className="text-white/70 text-sm leading-relaxed fade-in max-w-2xl" style={{animationDelay: '0.3s'}}>
                                    {theme.description}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Messages Area - SCROLLABLE CHAT MESSAGES ONLY */}
                    <div className="flex-1 overflow-y-auto px-12 py-8 space-y-6 scrollbar-thin scrollbar-thumb-clintra-teal/30 scrollbar-track-transparent" id="messages-container" ref={messagesContainerRef} style={{maxHeight: 'calc(100vh - 200px)', marginBottom: '100px'}}>
                        {messages.length > 0 && (
                            /* Messages - Prompts right, Responses left, all animated */
                            messages.map((msg, idx) => (
                                <div key={idx} className={`fade-in`} style={{animationDelay: `${idx * 0.15}s`}}>
                                    {msg.role === 'user' ? (
                                        /* User Prompt - Right aligned with SAME styling as response */
                                        <div className="flex justify-end slide-in-right">
                                            <div className={`max-w-md px-6 py-5 rounded-2xl bg-clintra-navy-dark/30 backdrop-blur-xl border ${theme.borderColor} shadow-xl hover:shadow-${theme.navColor}/5 transition-all duration-300`}>
                                                <p className="text-white/95 font-medium text-sm leading-relaxed">
                                                    {msg.content}
                                                </p>
                                            </div>
                                        </div>
                                    ) : (
                                        /* AI Response - Left aligned with enhanced formatting */
                                        <div className="flex justify-start slide-in-left">
                                            <div className={`max-w-4xl px-6 py-5 rounded-2xl bg-clintra-navy-dark/30 backdrop-blur-xl border ${theme.borderColor} shadow-xl hover:shadow-${theme.navColor}/5 transition-all duration-300`}>
                                                <div className="text-white/95 text-sm leading-relaxed space-y-3">
                                                    <div dangerouslySetInnerHTML={{ __html: formatContent(msg.content || '') }} />
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                        
                        {/* Loading Message Animation */}
                        {isLoading && (
                            <div className="flex justify-start slide-in-left">
                                <div className={`max-w-4xl px-6 py-5 rounded-2xl bg-clintra-navy-dark/30 backdrop-blur-xl border ${theme.borderColor} shadow-xl`}>
                                    <div className="flex items-center space-x-3">
                                        <div className="flex space-x-1">
                                            <div className="w-2 h-2 bg-clintra-cyan rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                                            <div className="w-2 h-2 bg-clintra-teal rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                                            <div className="w-2 h-2 bg-clintra-purple rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                                        </div>
                                        <span className="text-white/70 text-sm font-medium">Generating response...</span>
                                    </div>
                                </div>
                            </div>
                        )}
                        
                        {/* Auto-scroll anchor */}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Unified Search Bar - FIXED AT BOTTOM, PERFECTLY ALIGNED */}
                    <div className={`fixed bottom-0 z-10`} style={{left: '180px', right: '200px'}}>
                        <div className={`px-6 py-4 bg-clintra-navy-dark/50 backdrop-blur-xl border-t ${theme.borderColor} transition-all duration-500`}>
                            <div className="flex items-center space-x-3 w-full">
                            {/* Unified Input with Attachment Inside */}
                            <div className={`flex-1 flex items-center bg-clintra-navy-lighter border ${theme.borderColor} ${theme.hoverBorder} rounded-full px-4 py-2 focus-within:ring-2 focus-within:ring-${theme.navColor}/20 transition-all duration-300`}>
                                <input
                                    type="text"
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    placeholder={`Ask me anything about ${theme.title.toLowerCase()}...`}
                                    className={`flex-1 bg-transparent ${theme.textColor} placeholder-white/40 focus:outline-none text-sm`}
                                    onKeyPress={(e) => {
                                        if (e.key === 'Enter' && !e.shiftKey) {
                                            e.preventDefault();
                                            onSendMessage && onSendMessage(e);
                                        }
                                    }}
                                    disabled={isLoading}
                                />
                                
                                {/* Attachment Button - FUNCTIONAL */}
                                <button 
                                    onClick={() => {
                                        const fileInput = document.createElement('input');
                                        fileInput.type = 'file';
                                        fileInput.accept = '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.webp';
                                        fileInput.onchange = (e) => {
                                            const file = e.target.files[0];
                                            if (file) {
                                                if (window.handleFileSelect) {
                                                    window.handleFileSelect(file);
                                                }
                                            }
                                        };
                                        fileInput.click();
                                    }}
                                    className={`p-2 hover:bg-white/5 rounded-full transition-all cursor-pointer`}
                                    title="Attach file"
                                >
                                    <svg className={`w-4 h-4 ${theme.textColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                                    </svg>
                                </button>
                            </div>
                            
                            {/* Send Button - Circular with Arrow */}
                            <button 
                                className={`bg-gradient-to-r ${theme.bgGradient} w-10 h-10 rounded-full text-white hover:shadow-lg hover:scale-110 transition-all duration-300 flex items-center justify-center flex-shrink-0 ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                                onClick={(e) => onSendMessage && onSendMessage(e)}
                                disabled={isLoading || !inputValue.trim()}
                            >
                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                                </svg>
                            </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* ═══════════════════════════════════════ */}
                {/* RIGHT SECTION: Features - REDUCED SIZE */}
                {/* ═══════════════════════════════════════ */}
                <div className="bg-clintra-navy-light border-l border-clintra-teal/20 p-3 overflow-y-auto">
                    <h2 className="text-white font-semibold mb-4 text-sm">Features</h2>
                    
                    <div className="space-y-4">
                        {/* Team Workspace - FUNCTIONAL with better UI */}
                        <button 
                            onClick={() => {
                                console.log('🖱️ Team Workspace button clicked');
                                if (window.openTeamWorkspace) {
                                    console.log('🔄 Calling window.openTeamWorkspace...');
                                    window.openTeamWorkspace();
                                } else {
                                    console.error('❌ window.openTeamWorkspace not available');
                                }
                            }}
                            className="w-full bg-clintra-navy-lighter border border-clintra-teal/20 p-3 rounded-lg hover:border-clintra-teal/40 transition-all cursor-pointer text-left"
                        >
                            <div className="flex items-center space-x-2">
                                <span className="text-clintra-cyan">👥</span>
                                <span className="text-white font-medium text-xs">Team Workspace</span>
                            </div>
                        </button>
                        
                        <div className="border-t border-clintra-teal/20 my-3"></div>
                        
                        {/* Literature Mode - REDUCED SIZE */}
                        <button
                            onClick={() => onModeChange('literature')}
                            className={`w-full p-2 rounded-lg text-white font-semibold transition-all transform hover:scale-105 text-xs ${
                                activeMode === 'literature'
                                    ? 'bg-gradient-to-r from-clintra-teal to-clintra-cyan shadow-2xl glow-literature'
                                    : 'bg-clintra-navy-lighter border border-clintra-teal/30 hover:bg-clintra-teal/10'
                            }`}
                        >
                            🔍 Literature
                        </button>
                        
                        {/* Hypothesis Mode - REDUCED SIZE */}
                        <button
                            onClick={() => onModeChange('hypothesis')}
                            className={`w-full p-2 rounded-lg text-white font-semibold transition-all transform hover:scale-105 text-xs ${
                                activeMode === 'hypothesis'
                                    ? 'bg-gradient-to-r from-clintra-purple-dark to-clintra-purple shadow-2xl glow-hypothesis'
                                    : 'bg-clintra-navy-lighter border border-clintra-purple/30 text-clintra-purple hover:bg-clintra-purple/10'
                            }`}
                        >
                            🧬 Hypothesis
                        </button>
                        
                        {/* Download Mode - REDUCED SIZE */}
                        <button
                            onClick={() => onModeChange('download')}
                            className={`w-full p-2 rounded-lg text-white font-semibold transition-all transform hover:scale-105 text-xs ${
                                activeMode === 'download'
                                    ? 'bg-gradient-to-r from-clintra-gold-dark to-clintra-gold shadow-2xl glow-download'
                                    : 'bg-clintra-navy-lighter border border-clintra-gold/30 text-clintra-gold hover:bg-clintra-gold/10'
                            }`}
                        >
                            📥 Download
                        </button>
                        
                        {/* 3D Viewer - REDUCED SIZE */}
                        <button 
                            onClick={() => onNavigate && onNavigate('molecule-viewer')}
                            className="w-full p-2 rounded-lg bg-clintra-navy-lighter border border-clintra-teal/30 text-white font-medium hover:bg-clintra-teal/10 transition-all hover:border-clintra-teal cursor-pointer text-xs"
                        >
                            🔬 3D Viewer
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatPage;

