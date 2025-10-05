import React, { useState } from 'react';
import ClintraLogo from './ClintraLogo';

const Homepage = ({ user, onNavigate, onLogout }) => {
    const [showMenu, setShowMenu] = useState(false);

    // Close menu when clicking outside
    React.useEffect(() => {
        const handleClickOutside = (e) => {
            if (showMenu && !e.target.closest('.menu-container')) {
                setShowMenu(false);
            }
        };
        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    }, [showMenu]);

    return (
        <div className="min-h-screen bg-clintra-navy-darker">
            {/* 🎨 ENHANCED NAVBAR - ULTRA DARK & SMOOTH */}
            <nav className="bg-clintra-navy-dark border-b border-clintra-teal/30 px-8 py-4 backdrop-blur-sm">
                <div className="flex items-center justify-between">
                    {/* Left: Logo - Enhanced with animations */}
                    <button 
                        onClick={() => onNavigate('homepage')}
                        className="flex items-center space-x-3 hover:opacity-90 transition-all duration-300 group"
                    >
                        <div className="group-hover:scale-110 transition-transform duration-300">
                            <ClintraLogo size="lg" />
                        </div>
                        <span className="text-xl font-black text-clintra-cyan-bright tracking-wider group-hover:text-clintra-cyan transition-colors duration-300">CLINTRA</span>
                    </button>

                    {/* Center: Navigation - Enhanced */}
                    <div className="flex items-center space-x-8">
                        <button 
                            onClick={() => onNavigate('chat')}
                            className="text-white/90 hover:text-clintra-cyan-bright transition-all duration-300 text-base font-semibold hover:scale-105 relative group"
                        >
                            Chat
                            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-clintra-cyan group-hover:w-full transition-all duration-300"></span>
                        </button>
                        <button 
                            onClick={() => onNavigate('molecule-viewer')}
                            className="text-white/90 hover:text-clintra-cyan-bright transition-all duration-300 text-base font-semibold hover:scale-105 relative group"
                        >
                            3D View
                            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-clintra-cyan group-hover:w-full transition-all duration-300"></span>
                        </button>
                        <button 
                            onClick={() => onNavigate('about')}
                            className="text-white/90 hover:text-clintra-cyan-bright transition-all duration-300 text-base font-semibold hover:scale-105 relative group"
                        >
                            About us
                            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-clintra-cyan group-hover:w-full transition-all duration-300"></span>
                        </button>
                    </div>

                    {/* Right: User Menu - Enhanced */}
                    <div className="flex items-center space-x-4 relative menu-container">
                        <div className="text-white/90 text-base font-medium">
                            Welcome, <span className="text-clintra-cyan-bright font-semibold">{user?.username || 'User'}</span>
                        </div>
                        <button 
                            onClick={(e) => {
                                e.stopPropagation();
                                setShowMenu(!showMenu);
                            }}
                            className="w-8 h-8 bg-clintra-navy border border-clintra-teal/30 rounded-xl flex items-center justify-center hover:bg-clintra-teal/20 hover:scale-110 transition-all duration-300 group"
                        >
                            <div className="flex flex-col space-y-1">
                                <div className="w-4 h-0.5 bg-clintra-cyan group-hover:bg-clintra-cyan-bright transition-colors"></div>
                                <div className="w-4 h-0.5 bg-clintra-cyan group-hover:bg-clintra-cyan-bright transition-colors"></div>
                                <div className="w-4 h-0.5 bg-clintra-cyan group-hover:bg-clintra-cyan-bright transition-colors"></div>
                            </div>
                        </button>

                        {/* Enhanced Dropdown Menu */}
                        {showMenu && (
                            <div className="absolute right-0 top-12 w-56 bg-clintra-navy border border-clintra-teal/40 rounded-2xl shadow-2xl z-50 overflow-hidden backdrop-blur-sm slide-in-right">
                                <button
                                    onClick={() => {
                                        setShowMenu(false);
                                        // Navigate to account settings
                                    }}
                                    className="w-full px-4 py-3 text-left text-white text-sm hover:bg-clintra-teal/15 transition-all duration-300 flex items-center space-x-3 group"
                                >
                                    <svg className="w-5 h-5 text-clintra-cyan group-hover:text-clintra-cyan-bright transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    </svg>
                                    <span className="font-medium">Account Settings</span>
                                </button>
                                
                                <div className="border-t border-clintra-teal/30"></div>
                                
                                <button
                                    onClick={() => {
                                        setShowMenu(false);
                                        onLogout();
                                    }}
                                    className="w-full px-4 py-3 text-left text-red-400 text-sm hover:bg-red-500/15 transition-all duration-300 flex items-center space-x-3 group"
                                >
                                    <svg className="w-5 h-5 text-red-400 group-hover:text-red-300 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                                    </svg>
                                    <span className="font-medium">Logout</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </nav>

            {/* 🎨 ENHANCED MAIN CONTENT - ULTRA DARK & SMOOTH */}
            <div className="container mx-auto px-12 py-20">
                <div className="grid grid-cols-2 gap-20 items-center">
                    {/* Left: Enhanced Welcome Content */}
                    <div className="space-y-10 fade-in">
                        <h1 className="text-6xl font-black text-white leading-tight tracking-tight">
                            WELCOME
                            <br />
                            <span className="text-clintra-cyan-bright bg-gradient-to-r from-clintra-cyan to-clintra-cyan-bright bg-clip-text text-transparent">USER</span>
                        </h1>
                        
                        <p className="text-white/90 text-xl leading-relaxed max-w-2xl font-medium">
                            Clintra accelerates biomedical research with AI-powered literature search, 
                            hypothesis generation, and molecular data access. Explore cutting-edge research, 
                            analyze compounds, and visualize 3D molecular structures - all in one platform.
                        </p>

                        <div className="flex space-x-6">
                            <button 
                                onClick={() => onNavigate('about')}
                                className="px-10 py-5 bg-clintra-navy border-2 border-clintra-teal/50 text-clintra-cyan rounded-2xl font-bold text-lg hover:bg-clintra-teal/10 hover:border-clintra-teal hover:scale-105 transition-all duration-300 group"
                            >
                                <span>Read more →</span>
                            </button>
                            <button 
                                onClick={() => onNavigate('chat')}
                                className="px-10 py-5 bg-gradient-to-r from-clintra-teal to-clintra-cyan border-2 border-clintra-cyan text-white rounded-2xl font-bold text-lg hover:from-clintra-cyan hover:to-clintra-teal hover:scale-110 hover:shadow-xl transition-all duration-300 group shadow-lg"
                            >
                                <span className="flex items-center space-x-2">
                                    <span>Start Research</span>
                                    <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                    </svg>
                                </span>
                            </button>
                        </div>

                        {/* Sponsor Tech Showcase - Added Here */}
                        <div className="pt-8">
                            <p className="text-white/60 text-sm mb-3">Powered by</p>
                            <div className="flex space-x-4">
                                <div className="flex items-center space-x-2 bg-clintra-navy-lighter px-3 py-2 rounded-lg">
                                    <div className="w-6 h-6 bg-gradient-to-r from-orange-400 to-orange-600 rounded flex items-center justify-center">
                                        <span className="text-white font-bold text-xs">C</span>
                                    </div>
                                    <span className="text-white text-sm font-medium">Cerebras</span>
                                </div>
                                <div className="flex items-center space-x-2 bg-clintra-navy-lighter px-3 py-2 rounded-lg">
                                    <div className="w-6 h-6 bg-gradient-to-r from-purple-500 to-purple-700 rounded flex items-center justify-center">
                                        <span className="text-white font-bold text-xs">L</span>
                                    </div>
                                    <span className="text-white text-sm font-medium">Llama</span>
                                </div>
                                <div className="flex items-center space-x-2 bg-clintra-navy-lighter px-3 py-2 rounded-lg">
                                    <div className="w-6 h-6 bg-gradient-to-r from-blue-400 to-blue-600 rounded flex items-center justify-center">
                                        <span className="text-white font-bold text-xs">D</span>
                                    </div>
                                    <span className="text-white text-sm font-medium">Docker MCP</span>
                                </div>
                            </div>
                        </div>

                        {/* Feature Indicators */}
                        <div className="flex space-x-4 pt-4">
                            <div className="w-16 h-16 bg-clintra-navy-lighter rounded-xl border border-clintra-teal/30"></div>
                            <div className="w-12 h-12 bg-clintra-navy-lighter rounded-xl border border-clintra-teal/30 mt-2"></div>
                            <div className="w-20 h-20 bg-clintra-navy-lighter rounded-xl border border-clintra-teal/30"></div>
                            <div className="w-12 h-12 bg-clintra-navy-lighter rounded-xl border border-clintra-teal/30 mt-4"></div>
                        </div>
                    </div>

                    {/* Right: Bio Visual - DNA HELIX */}
                    <div className="relative float">
                        {/* DNA/Circuit Brain Visual */}
                        <div className="w-full h-96 bg-gradient-to-br from-clintra-teal/20 to-clintra-cyan/20 rounded-3xl flex items-center justify-center backdrop-blur-sm border border-clintra-teal/30 shadow-2xl">
                            {/* Animated Circuit Pattern */}
                            <svg className="w-80 h-80 text-clintra-cyan opacity-80" fill="none" stroke="currentColor" viewBox="0 0 200 200">
                                {/* DNA Helix */}
                                <path strokeWidth="3" d="M60 40 Q80 60, 60 80 Q40 100, 60 120 Q80 140, 60 160" className="animate-pulse" />
                                <path strokeWidth="3" d="M140 40 Q120 60, 140 80 Q160 100, 140 120 Q120 140, 140 160" className="animate-pulse" style={{animationDelay: '0.5s'}} />
                                
                                {/* Connecting lines */}
                                <line x1="60" y1="40" x2="140" y2="40" strokeWidth="2" className="opacity-60" />
                                <line x1="60" y1="80" x2="140" y2="80" strokeWidth="2" className="opacity-60" />
                                <line x1="60" y1="120" x2="140" y2="120" strokeWidth="2" className="opacity-60" />
                                <line x1="60" y1="160" x2="140" y2="160" strokeWidth="2" className="opacity-60" />
                                
                                {/* Nodes */}
                                <circle cx="60" cy="40" r="4" fill="currentColor" />
                                <circle cx="140" cy="40" r="4" fill="currentColor" />
                                <circle cx="60" cy="80" r="4" fill="currentColor" />
                                <circle cx="140" cy="80" r="4" fill="currentColor" />
                                <circle cx="60" cy="120" r="4" fill="currentColor" />
                                <circle cx="140" cy="120" r="4" fill="currentColor" />
                                <circle cx="60" cy="160" r="4" fill="currentColor" />
                                <circle cx="140" cy="160" r="4" fill="currentColor" />
                            </svg>
                        </div>
                        
                        {/* Floating stats/badges */}
                        <div className="absolute -top-4 -right-4 bg-clintra-navy-lighter border border-clintra-cyan/50 rounded-2xl p-4 shadow-xl">
                            <div className="text-clintra-cyan font-bold text-2xl">1000+</div>
                            <div className="text-white/60 text-sm">Research Papers</div>
                        </div>
                        
                        <div className="absolute -bottom-4 -left-4 bg-clintra-navy-lighter border border-clintra-purple/50 rounded-2xl p-4 shadow-xl">
                            <div className="text-clintra-purple font-bold text-2xl">AI</div>
                            <div className="text-white/60 text-sm">Powered</div>
                        </div>
                    </div>
                </div>

                {/* Enhanced Feature Cards */}
                <div className="grid grid-cols-3 gap-10 mt-32">
                    {/* Literature Card - Enhanced */}
                    <div 
                        onClick={() => {
                            onNavigate('chat');
                            // Set literature mode when navigating to chat
                            if (window.setActiveMode) {
                                window.setActiveMode('literature');
                            }
                        }}
                        className="bg-clintra-navy border border-clintra-teal/40 rounded-3xl p-10 hover:border-clintra-teal-bright hover:shadow-2xl hover:scale-105 transition-all duration-500 cursor-pointer group bounce-in relative overflow-hidden"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-clintra-teal/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                        <div className="relative z-10">
                            <div className="w-20 h-20 bg-gradient-to-br from-clintra-teal to-clintra-cyan-bright rounded-2xl flex items-center justify-center mb-8 group-hover:scale-110 group-hover:rotate-6 transition-all duration-500 shadow-xl">
                                <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                                </svg>
                            </div>
                            <h3 className="text-3xl font-black text-white mb-4 group-hover:text-clintra-cyan-bright transition-colors duration-300">Literature Search</h3>
                            <p className="text-white/80 text-lg leading-relaxed font-medium">Search and analyze thousands of research papers with AI assistance</p>
                        </div>
                    </div>

                    {/* Hypothesis Card - Enhanced */}
                    <div 
                        onClick={() => {
                            onNavigate('chat');
                            // Set hypothesis mode when navigating to chat
                            if (window.setActiveMode) {
                                window.setActiveMode('hypothesis');
                            }
                        }}
                        className="bg-clintra-navy border border-clintra-purple/40 rounded-3xl p-10 hover:border-clintra-purple-bright hover:shadow-2xl hover:scale-105 transition-all duration-500 cursor-pointer group scale-in-rotate relative overflow-hidden"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-clintra-purple/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                        <div className="relative z-10">
                            <div className="w-20 h-20 bg-gradient-to-br from-clintra-purple to-clintra-purple-bright rounded-2xl flex items-center justify-center mb-8 group-hover:scale-110 group-hover:rotate-6 transition-all duration-500 shadow-xl">
                                <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                                </svg>
                            </div>
                            <h3 className="text-3xl font-black text-white mb-4 group-hover:text-clintra-purple-bright transition-colors duration-300">Hypothesis Generation</h3>
                            <p className="text-white/80 text-lg leading-relaxed font-medium">Generate AI-powered research hypotheses with citations</p>
                        </div>
                    </div>

                    {/* Download Data Card - Enhanced */}
                    <div 
                        onClick={() => {
                            onNavigate('chat');
                            // Set download mode when navigating to chat
                            if (window.setActiveMode) {
                                window.setActiveMode('download');
                            }
                        }}
                        className="bg-clintra-navy border border-clintra-gold/40 rounded-3xl p-10 hover:border-clintra-gold-bright hover:shadow-2xl hover:scale-105 transition-all duration-500 cursor-pointer group slide-in-right relative overflow-hidden"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-clintra-gold/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                        <div className="relative z-10">
                            <div className="w-20 h-20 bg-gradient-to-br from-clintra-gold-dark to-clintra-gold-bright rounded-2xl flex items-center justify-center mb-8 group-hover:scale-110 group-hover:rotate-6 transition-all duration-500 shadow-xl">
                                <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                                </svg>
                            </div>
                            <h3 className="text-3xl font-black text-white mb-4 group-hover:text-clintra-gold-bright transition-colors duration-300">Download Data</h3>
                            <p className="text-white/80 text-lg leading-relaxed font-medium">Access compound and protein structure data from PubChem & PDB</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Dotted pattern decoration */}
            <div className="fixed top-0 right-0 w-64 h-64 opacity-20 pointer-events-none">
                <div className="grid grid-cols-8 gap-2 p-8">
                    {[...Array(64)].map((_, i) => (
                        <div key={i} className="w-1 h-1 bg-clintra-cyan rounded-full"></div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Homepage;
