import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import DynamicLogin from './components/DynamicLogin';
import Homepage from './components/Homepage';
import ChatPage from './components/ChatPage';
import Fixed3DViewer from './components/Fixed3DViewer';
import ThemeToggle from './components/ThemeToggle';
import MessageSearch from './components/MessageSearch';
import ExportImport from './components/ExportImport';
import TeamWorkspaceModal from './components/TeamWorkspaceModal';

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
    const [showSearch, setShowSearch] = useState(false);
    const [showProfileMenu, setShowProfileMenu] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    const [isAnalyzingFile, setIsAnalyzingFile] = useState(false);
    
    const [currentPage, setCurrentPage] = useState('homepage'); // 'homepage', 'chat', 'molecule-viewer', 'about'
    const [previousPage, setPreviousPage] = useState('homepage'); // Track where user came from
    
    // 🆕 NEW TEAM WORKSPACE MODAL STATE
    const [showTeamWorkspaceModal, setShowTeamWorkspaceModal] = useState(false);
    
    const handleNavigate = (page) => {
        setPreviousPage(currentPage); // Save current page before navigating
        setCurrentPage(page);
        // Save current page to localStorage
        localStorage.setItem('currentPage', page);
        localStorage.setItem('previousPage', currentPage);
    };
    
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);

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
        const savedPage = localStorage.getItem('currentPage');
        const savedPreviousPage = localStorage.getItem('previousPage');
        
        if (token && userData) {
            setUser(JSON.parse(userData));
            // Restore the page user was on
            if (savedPage) {
                setCurrentPage(savedPage);
            }
            if (savedPreviousPage) {
                setPreviousPage(savedPreviousPage);
            }
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
            // No initial welcome message - just empty chat
            setMessages([]);
        }
    }, [user]);


    const createNewChatSession = async () => {
        try {
            const token = localStorage.getItem('token');
            
            // Check if token exists
            if (!token) {
                console.error('❌ No authentication token found');
                setError('Please log in again to create chat sessions.');
                return;
            }
            
            console.log('🔑 Creating chat session with token:', token.substring(0, 20) + '...');
            
            const response = await axios.post(`${API_URL}/api/chat/sessions`, {
                title: 'New Chat'
            }, {
                headers: { Authorization: `Bearer ${token}` }
            });
            
            setCurrentSessionId(response.data.id);
            setChatSessions(prev => [response.data, ...prev]);
            setMessages([]);
            setError(null);
            console.log('✅ Chat session created successfully:', response.data.id);
        } catch (error) {
            console.error('Error creating chat session:', error);
            
            // Handle specific authentication errors
            if (error.response?.status === 401) {
                console.error('❌ Authentication failed - token may be expired');
                setError('Your session has expired. Please log in again.');
                // Optionally redirect to login
                handleLogout();
            } else {
                setError('Failed to create new chat session. Please try again.');
            }
        }
    };

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            // Check file type and size
            const maxSize = 10 * 1024 * 1024; // 10MB
            const allowedTypes = [
                'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
                'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/msword'
            ];
            
            if (file.size > maxSize) {
                setError('File size must be less than 10MB');
                return;
            }
            
            if (!allowedTypes.includes(file.type)) {
                setError('Supported file types: Images (JPG, PNG, GIF, WebP), PDF, Word documents');
                return;
            }
            
            setSelectedFile(file);
            setError(null);
        }
    };

    const handleRemoveFile = () => {
        setSelectedFile(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const analyzeFile = async () => {
        if (!selectedFile) return;
        
        setIsAnalyzingFile(true);
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('query', inputValue.trim());
        
        try {
            const response = await axios.post(`${API_URL}/api/analyze-file`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            const newMessage = {
                id: Date.now(),
                type: 'file_analysis',
                query: inputValue.trim() || 'File analysis',
                file_info: response.data.file_info,
                analysis: response.data.analysis,
                primary_ai: response.data.primary_ai,
                enhancement_ai: response.data.enhancement_ai,
                sponsor_tech: response.data.sponsor_tech,
                timestamp: new Date().toISOString()
            };
            
            setMessages(prev => [...prev, newMessage]);
            setInputValue('');
            setSelectedFile(null);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
            
        } catch (error) {
            console.error('File analysis error:', error);
            setError(error.response?.data?.detail || 'Failed to analyze file');
        } finally {
            setIsAnalyzingFile(false);
        }
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        
        // If there's a file selected, analyze it instead
        if (selectedFile) {
            await analyzeFile();
            return;
        }
        
        if (!inputValue.trim() || isLoading || !user || !isOnline) return;

        const userMessage = {
            id: Date.now(),
            role: 'user',
            content: inputValue,
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        const currentInput = inputValue;
        setInputValue('');
        setIsLoading(true);
        setError(null);
        console.log('🚀 Starting request, isLoading set to true');

        // 🔥 PERSISTENT MEMORY: Ensure session exists before sending message
        if (!currentSessionId && user) {
            try {
                const token = localStorage.getItem('token');
                const sessionResponse = await axios.post(`${API_URL}/api/chat/sessions`, {
                    title: `New Chat - ${new Date().toLocaleDateString()}`,
                    description: 'Auto-created session'
                }, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setCurrentSessionId(sessionResponse.data.id);
                console.log('✅ Auto-created session for first message');
            } catch (sessionError) {
                console.warn('Could not auto-create session:', sessionError);
            }
        }

        try {
            let response;
            let assistantMessage; // Declare in outer scope
            
            // Check if user has selected a specific mode (not literature)
            // OR if the message looks like a specific research request
            const isSpecificMode = activeMode !== 'literature';
            const isResearchKeywords = /\b(search|find|literature|papers|studies|research|hypothesis|generate|download|graph|visualize|analyze)\b/i.test(currentInput);
            const isCasualMessage = /^(hi|hello|hey|what's up|how are you|good morning|good evening|thanks|thank you|bye|goodbye)$/i.test(currentInput.trim());
            
            // ROUTE TO SPECIFIC ENDPOINTS BASED ON ACTIVE MODE
            if (activeMode === 'download') {
                // Use download endpoint for download mode
                response = await axios.post(`${API_URL}/api/download`, {
                    compound_name: currentInput
                });
            } else if (activeMode === 'hypothesis') {
                // Use hypothesis endpoint for hypothesis mode
                response = await axios.post(`${API_URL}/api/hypothesis`, {
                    text: currentInput
                });
            } else {
                // Use smart-chat endpoint for literature mode and general queries
                response = await axios.post(`${API_URL}/api/smart-chat`, {
                    message: currentInput
                });
            }

            // Handle different endpoint response formats
            let responseContent = '';
            let aiModel = 'Cerebras Llama 3.1-8B';
            let sponsorTech = 'Cerebras AI + Docker MCP';
            
            if (activeMode === 'download') {
                // Download endpoint returns structured data - format it properly
                responseContent = formatResponse(response.data, 'download');
                aiModel = response.data.ai_model || 'Cerebras Llama 3.1-8B';
                sponsorTech = response.data.sponsor_tech || 'Docker MCP Gateway microservices';
            } else if (activeMode === 'hypothesis') {
                // Hypothesis endpoint returns hypothesis text
                responseContent = response.data.hypothesis || 'Hypothesis generated';
                aiModel = response.data.ai_model || 'Cerebras Llama 3.1-8B';
                sponsorTech = response.data.sponsor_tech || 'Cerebras AI + Docker MCP';
            } else {
                // Smart-chat endpoint format
                if (response.data.type === 'research_query') {
                    responseContent = response.data.rag_summary || response.data.response || 'Analysis completed';
                } else {
                    responseContent = response.data.response || 'Response generated';
                }
                aiModel = response.data.ai_model || 'Cerebras Llama 3.1-8B';
                sponsorTech = response.data.sponsor_tech || 'Cerebras AI + Docker MCP';
            }
            
            assistantMessage = {
                id: Date.now() + 1,
                role: 'assistant',
                content: responseContent,
                timestamp: new Date().toISOString(),
                mode: activeMode,
                ai_model: aiModel,
                sponsor_tech: sponsorTech
            };

            setMessages(prev => [...prev, assistantMessage]);

            // 🚀 ENHANCED MEMORY: Save conversation to chat history (only if session exists)
            console.log('🔍 Checking if should save message to history:');
            console.log('- assistantMessage:', !!assistantMessage);
            console.log('- currentSessionId:', currentSessionId);
            console.log('- includes fallback:', currentSessionId?.includes('fallback'));
            console.log('- includes guest:', currentSessionId?.includes('guest'));
            
            if (assistantMessage && currentSessionId && !currentSessionId.includes('fallback') && !currentSessionId.includes('guest')) {
                console.log('✅ All conditions met, calling saveMessageToHistory...');
                try {
                    await saveMessageToHistory(currentInput, assistantMessage.content, activeMode);
                } catch (historyError) {
                    // Silently fail - don't show error to user for history save failures
                    console.warn('❌ Failed to save message to history:', historyError);
                    // If auth error, might need to re-login
                    if (historyError.response?.status === 401) {
                        console.warn('⚠️ Auth token invalid - history not saved');
                    }
                }
            } else {
                console.log('❌ Not saving message to history - conditions not met');
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
            console.log('✅ Request completed, isLoading set to false');
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('currentPage');
        setUser(null);
        setMessages([]);
        setChatSessions([]);
        setCurrentSessionId(null);
        setCurrentPage('homepage');
        setError(null);
    };

    const clearError = () => {
        setError(null);
    };

    const handleSearchMessage = (message) => {
        // Scroll to the message (simplified - in a real app you'd need message refs)
        console.log('Searching for message:', message);
        // You could implement scroll-to-message functionality here
    };

    const handleImportMessages = (importedMessages) => {
        // Add imported messages to current chat
        setMessages(prev => [...prev, ...importedMessages]);
    };

    // 🚀 ENHANCED MEMORY & CHAT HISTORY FEATURES WITH AUTO-SAVE
    const createNewChat = async () => {
        try {
            if (user) {
                const token = localStorage.getItem('token');
                
                // 🔥 DEBUG: Check token
                if (!token) {
                    console.error('❌ No token found! User needs to log in again.');
                    setError('Session expired. Please log in again.');
                    handleLogout();
                    return;
                }
                
                console.log('✅ Token found, creating new chat...');
                
                // 🔥 STEP 1: Save and finalize current chat session if it exists
                if (currentSessionId && messages.length > 1 && !currentSessionId.includes('fallback') && !currentSessionId.includes('guest')) {
                    console.log('💾 Saving current chat before creating new one...');
                    
                    // Extract context from all messages to generate smart title
                    const extractSessionContext = () => {
                        const allContent = messages.map(m => m.content).join(' ');
                        const diseases = allContent.match(/\b(diabetes|cancer|alzheimer|parkinson|heart disease|stroke|covid|influenza|hepatitis|HIV|AIDS|leukemia|lymphoma|melanoma)\b/gi) || [];
                        const drugs = allContent.match(/\b(insulin|metformin|aspirin|warfarin|caffeine|morphine|paracetamol|ibuprofen|chemotherapy|immunotherapy)\b/gi) || [];
                        const proteins = allContent.match(/\b([A-Z]{2,4}\d+|protein|enzyme|receptor|antibody)\b/g) || [];
                        const topics = allContent.match(/\b(treatment|therapy|diagnosis|mechanism|pathway|clinical trial|research)\b/gi) || [];
                        
                        return {
                            diseases: [...new Set(diseases.map(d => d.toLowerCase()))].slice(0, 2),
                            drugs: [...new Set(drugs.map(d => d.toLowerCase()))].slice(0, 2),
                            proteins: [...new Set(proteins)].slice(0, 2),
                            topics: [...new Set(topics.map(t => t.toLowerCase()))].slice(0, 2),
                            messageCount: messages.length
                        };
                    };
                    
                    const context = extractSessionContext();
                    
                    // Generate smart title based on content
                    let autoTitle = '';
                    if (context.diseases.length > 0) {
                        autoTitle = `${context.diseases[0].charAt(0).toUpperCase() + context.diseases[0].slice(1)}`;
                        if (context.drugs.length > 0) {
                            autoTitle += ` & ${context.drugs[0].charAt(0).toUpperCase() + context.drugs[0].slice(1)}`;
                        } else if (context.topics.length > 0) {
                            autoTitle += ` ${context.topics[0]}`;
                        }
                    } else if (context.drugs.length > 0) {
                        autoTitle = `${context.drugs[0].charAt(0).toUpperCase() + context.drugs[0].slice(1)} Research`;
                    } else if (context.topics.length > 0) {
                        autoTitle = `${context.topics[0].charAt(0).toUpperCase() + context.topics[0].slice(1)} Research`;
                    } else {
                        autoTitle = `Research Chat - ${new Date().toLocaleDateString()}`;
                    }
                    
                    // Update current session with auto-generated title
                    try {
                        await axios.patch(`${API_URL}/api/chat/sessions/${currentSessionId}`, {
                            title: autoTitle,
                            message_count: messages.length,
                            last_updated: new Date().toISOString()
                        }, {
                            headers: { Authorization: `Bearer ${token}` }
                        });
                        console.log(`✅ Current chat saved with title: "${autoTitle}"`);
                    } catch (saveError) {
                        console.warn('Could not save current session:', saveError);
                    }
                }
                
                // 🔥 STEP 2: Create new session
                const response = await axios.post(`${API_URL}/api/chat/sessions`, {
                    title: `New Research Chat`,
                    description: 'Research conversation - topic will be auto-detected'
                }, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                
                const newSession = response.data;
                setCurrentSessionId(newSession.id);
                setMessages([]); // Reset messages for new chat
                
                // Refresh sessions list to show the saved chat
                await loadChatSessions();
                
                console.log('✅ New chat created successfully - ready for new conversation');
            } else {
                // For guest users, just reset current chat
                setMessages([]);
                setCurrentSessionId(`guest_${Date.now()}`);
            }
        } catch (error) {
            console.error('Error creating new chat:', error);
            // Fallback: just reset messages
            setMessages([]);
            setCurrentSessionId(`fallback_${Date.now()}`);
        }
    };

    const loadChatSessions = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                console.warn('No token found for loading chat sessions');
                setChatSessions([]);
                return;
            }
            
            if (!user) {
                console.warn('No user found for loading chat sessions');
                setChatSessions([]);
                return;
            }
            
            console.log('🔍 Loading chat sessions...');
            const response = await axios.get(`${API_URL}/api/chat/sessions`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setChatSessions(response.data);
            console.log('✅ Chat sessions loaded:', response.data.length);
        } catch (error) {
            console.error('Error loading chat sessions:', error);
            if (error.response?.status === 401) {
                console.error('❌ Authentication failed - token may be expired');
                setError('Your session has expired. Please log in again.');
                handleLogout();
            }
            setChatSessions([]);
        }
    };

    const switchToSession = async (sessionId) => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                console.error('❌ No token found for switching session');
                return;
            }
            
            if (!user) {
                console.error('❌ No user found for switching session');
                return;
            }
            
            console.log(`🔄 Switching to session ${sessionId}...`);
            
            const response = await axios.get(`${API_URL}/api/chat/sessions/${sessionId}/messages`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            
            // Load messages from selected session with context awareness
            const sessionMessages = response.data.map(msg => ({
                id: msg.id,
                role: msg.role,
                content: msg.content,
                timestamp: msg.timestamp,
                mode: msg.mode,
                context_topics: msg.context_topics || [],
                isUser: msg.role === 'user'
            }));
            
            setMessages(sessionMessages);
            setCurrentSessionId(sessionId);
            
            console.log(`✅ Switched to session ${sessionId} with ${sessionMessages.length} messages`);
            
            // Also update the active mode based on the session content if needed
            if (sessionMessages.length > 0) {
                const lastMessage = sessionMessages[sessionMessages.length - 1];
                if (lastMessage.mode && lastMessage.mode !== activeMode) {
                    console.log(`🔄 Updating active mode to: ${lastMessage.mode}`);
                    setActiveMode(lastMessage.mode);
                }
            }
            
        } catch (error) {
            console.error('❌ Error switching to session:', error);
            if (error.response?.status === 401) {
                console.error('❌ Authentication failed during session switch');
                setError('Your session has expired. Please log in again.');
                handleLogout();
            }
        }
    };

    const saveMessageToHistory = async (message, response, mode) => {
        try {
            const token = localStorage.getItem('token');
            if (token && user && currentSessionId) {
                // 🔥 CONTEXT-AWARE MESSAGE SAVING
                
                // Extract key topics/research areas from the conversation
                const extractContext = (content) => {
                    const biomedicalTerms = content.match(/\[([a-zA-Z\s]+)\]/g) || [];
                    const proteins = content.match(/\b[A-Z]{1,2}\d+\b/g) || [];
                    const diseases = content.match(/\b(diabetes|cancer|alzheimer|parkinson|autism)\b/gi) || [];
                    const drugs = content.match(/\b(insulin|metformin|aspirin|warfarin|caffeine|morphine)\b/gi) || [];
                    
                    return {
                        biomedical_terms: biomedicalTerms.map(t => t.slice(1, -1)),
                        proteins: proteins.slice(0, 5), // Top 5 proteins
                        diseases: diseases.slice(0, 3),
                        drugs: drugs.slice(0, 3),
                        research_topics: [...new Set([...diseases, ...drugs])].slice(0, 5)
                    };
                };
                
                const context = extractContext(`${message} ${response}`);
                
                // Save user message with context
                const userMessage = {
                    content: message,
                    mode: mode,
                    role: 'user',
                    context_topics: context.research_topics,
                    timestamp: new Date().toISOString()
                };
                
                // Save assistant response with enhanced context
                const assistantMessage = {
                    content: response,
                    mode: mode,
                    role: 'assistant',
                    context_summary: {
                        key_subjects: context.research_topics,
                        mentioned_proteins: context.proteins,
                        diseases_discussed: context.diseases,
                        drugs_analyzed: context.drugs
                    },
                    response_length: response.length,
                    timestamp: new Date().toISOString()
                };
                
                // Send both messages to backend
                console.log('💾 Saving user message:', userMessage);
                const userResponse = await axios.post(`${API_URL}/api/chat/sessions/${currentSessionId}/messages`, userMessage, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                console.log('✅ User message saved:', userResponse.data);
                
                console.log('💾 Saving assistant message:', assistantMessage);
                const assistantResponse = await axios.post(`${API_URL}/api/chat/sessions/${currentSessionId}/messages`, assistantMessage, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                console.log('✅ Assistant message saved:', assistantResponse.data);
                
                // Update session context in backend with auto-generated title
                const autoTitle = context.research_topics.length > 0 
                    ? `Research: ${context.research_topics.slice(0, 2).join(' & ')}`
                    : `Research Session - ${new Date().toLocaleDateString()}`;
                
                // Update session title with auto-generated title
                try {
                    await axios.patch(`${API_URL}/api/chat/sessions/${currentSessionId}`, {
                        title: autoTitle,
                        description: `Research session focusing on: ${context.research_topics.join(', ')}`
                    }, {
                        headers: { Authorization: `Bearer ${token}` }
                    });
                    console.log('✅ Session title updated:', autoTitle);
                } catch (updateError) {
                    console.warn('Could not update session title:', updateError);
                    // Continue - this is not critical
                }
                
                console.log('Messages saved with context:', context.research_topics);
                
                // Refresh chat sessions to show updated titles
                await loadChatSessions();
            }
        } catch (error) {
            console.error('❌ Error saving to chat history:', error);
            if (error.response?.status === 401) {
                console.error('❌ Authentication failed during message save');
                setError('Your session has expired. Please log in again.');
                handleLogout();
            } else if (error.response?.status === 404) {
                console.error('❌ Chat session not found');
                setError('Chat session not found. Please create a new chat.');
            } else {
                console.error('❌ Failed to save message:', error.response?.data || error.message);
            }
        }
    };



    const formatSmartChatResponse = (data) => {
        // Debug log for troubleshooting "undefined" issue
        console.log('formatSmartChatResponse called with:', data);
        
        if (!data || typeof data !== 'object') {
            console.error('formatSmartChatResponse: data is null or not an object:', data);
            return "Error: Invalid response data received";
        }
        
        if (data.type === 'general_chat') {
            return `${data.response || "General chat response"}`;
        } else if (data.type === 'research_query') {
        // Format: Research Analysis + Real Links & Citations + Summary
        let content = `## 📊 Research Analysis\n\n${data.rag_summary}\n\n`;
        
        // Real Literature Links & Citations Section
        if (data.pubmed_articles && data.pubmed_articles.length > 0) {
            content += `## 📚 Literature & Citations\n\n`;
            content += `**PubMed Articles Analyzed (${data.pubmed_articles.length}):**\n\n`;
            data.pubmed_articles.forEach((article, index) => {
                content += `### ${index + 1}. ${article.title}\n\n`;
                content += `${article.abstract.substring(0, 300)}...\n\n`;
                if (article.url) {
                    content += `🔗 **[Read Full Article](${article.url})**\n\n`;
                }
                content += `---\n\n`;
            });
        }
        
        if (data.clinical_trials && data.clinical_trials.length > 0) {
            content += `## 🏥 Clinical Trials (${data.clinical_trials.length})\n\n`;
            data.clinical_trials.forEach((trial, index) => {
                content += `**${index + 1}. ${trial.title}**\n\n`;
                content += `Status: ${trial.status}\n`;
                content += `Phase: ${trial.phase}\n`;
                if (trial.url) {
                    content += `🔗 **[View Trial Details](${trial.url})**\n\n`;
                }
                content += `---\n\n`;
            });
        }
        
        // MAX LEVEL Features Section
        if (data.max_level_features) {
            const maxLevel = data.max_level_features;
            
            // Molecular Targeting Section
            if (maxLevel.molecular_targets) {
                content += `## 🎯 MAX LEVEL: Molecular Targeting\n\n`;
                
                // PDB Structures
                if (maxLevel.molecular_targets.pdb_structures && maxLevel.molecular_targets.pdb_structures.length > 0) {
                    content += `### 🏗️ **Structural Biology Targets (PDB Structures)**\n\n`;
                    maxLevel.molecular_targets.pdb_structures.forEach((pdb, index) => {
                        content += `**${index + 1}. ${pdb.pdb_id}** - ${pdb.title}\n`;
                        content += `📊 Resolution: ${pdb.resolution} | Method: ${pdb.experimental_method}\n`;
                        content += `🔗 **[View Structure](${pdb.pdb_url})** | **[Download PDB](${pdb.download_url})**\n\n`;
                    });
                }
                
                // PubChem Compounds
                if (maxLevel.molecular_targets.pubchem_compounds && maxLevel.molecular_targets.pubchem_compounds.length > 0) {
                    content += `### 💊 **Drug Compounds (PubChem)**\n\n`;
                    maxLevel.molecular_targets.pubchem_compounds.forEach((compound, index) => {
                        content += `**${index + 1}. ${compound.iupac_name}**\n`;
                        content += `🧬 Formula: ${compound.molecular_formula} | Weight: ${compound.molecular_weight} Da\n`;
                        content += `🔗 **[PubChem Profile](${compound.pubchem_url})**\n\n`;
                    });
                }
                
                // Feedback Mechanisms
                if (maxLevel.molecular_targets.feedback_mechanisms) {
                    const feedback = maxLevel.molecular_targets.feedback_mechanisms;
                    content += `### 🔄 **Biological Feedback Mechanisms**\n\n`;
                    content += `**${feedback.mechanism_name}**\n`;
                    content += `🧪 Components: ${feedback.components.join(' → ')}\n`;
                    content += `📋 Process: ${feedback.mechanism_description}\n\n`;
                    
                    content += `**🩺 Related Disorders:**\n`;
                    feedback.related_disorders.forEach(disorder => {
                        content += `- ${disorder}\n`;
                    });
                    content += `\n`;
                }
            }
            
            // Research Workflow Section
            if (maxLevel.research_workflow) {
                const workflow = maxLevel.research_workflow;
                content += `## 🚀 MAX LEVEL: Research Workflow\n\n`;
                content += `### 📋 **Bioinformatician Research Pathway** (${workflow.total_duration})\n\n`;
                
                workflow.steps.forEach((step, index) => {
                    content += `**Step ${step.step}: ${step.name}**\n`;
                    content += `⚒️ Tools: ${Array.isArray(step.tools) ? step.tools.join(', ') : step.tools}\n`;
                    content += `⏱️ Duration: ${step.duration}\n\n`;
                });
                
                content += `### 🛠️ **Essential Bioinformatics Tools**\n`;
                workflow.tools_summary.forEach(tool => {
                    content += `- ${tool}\n`;
                });
                content += `\n`;
            }
            
            // Visualization Links
            if (maxLevel.visualization_links && Object.keys(maxLevel.visualization_links).length > 0) {
                content += `## 📊 MAX LEVEL: Interactive Visualizations\n\n`;
                Object.entries(maxLevel.visualization_links).forEach(([platform, url]) => {
                    content += `🔗 **[Create Diagram on ${platform}](${url})**\n`;
                });
                content += `\n`;
            }
        }
        
        // FEATURE 1: DYNAMIC AI-GENERATED FEEDBACK MECHANISMS  
        if (data.feature_1_feedback) {
            const feedback = data.feature_1_feedback;
            content += `## 🔄 FEATURE 1: Biological Feedback Mechanisms\n\n`;
            
            content += `### **${feedback.mechanism_name}**\n\n`;
            content += `🧪 **Components**: ${Array.isArray(feedback.components) ? feedback.components.join(' → ') : feedback.components}\n`;
            content += `📋 **Process**: ${feedback.mechanism_description}\n\n`;
            
            content += `### 🩺 **Related Disorders**\n`;
            if (Array.isArray(feedback.related_disorders)) {
                feedback.related_disorders.forEach(disorder => {
                    content += `- ${disorder}\n`;
                });
            } else {
                content += `- ${feedback.related_disorders}\n`;
            }
            content += `\n`;
            
            content += `### 🧬 **Molecular Targets**\n`;
            if (typeof feedback.molecular_targets === 'object' && feedback.molecular_targets !== null) {
                Object.entries(feedback.molecular_targets).forEach(([molecule, target]) => {
                    content += `- **${molecule}**: ${target}\n`;
                });
            } else {
                content += `- ${feedback.molecular_targets}\n`;
            }
            content += `\n`;
            
            // Show AI generation info if available
            if (feedback.ai_generated) {
                content += `### 🔬 **Analysis Details**\n`;
                content += `✅ **AI-Generated**: Dynamic analysis using Cerebras Llama\n`;
                content += `📚 **Data Source**: ${feedback.literature_source || 'Literature-based analysis'}\n`;
                content += `🧠 **Method**: Advanced AI-driven pattern recognition\n\n`;
            }
        }
        
        // FEATURE 2: PDB STRUCTURE SUGGESTIONS
        if (data.feature_2_pdb) {
            const pdb = data.feature_2_pdb;
            content += `## 🧬 FEATURE 2: PDB Structure Analysis\n\n`;
            
            content += `### **${pdb.query_context}**\n\n`;
            content += `📊 **${pdb.structures_found} protein structures** identified from RCSB PDB database\n\n`;
            
            content += `### 🏗️ **Structural Biology Targets**\n`;
            pdb.structures.forEach((structure, index) => {
                content += `**${index + 1}. ${structure.pdb_id}** - ${structure.title}\n`;
                content += `📋 Resolution: ${structure.resolution}Å | Method: ${structure.method}\n`;
                content += `🧪 Organism: ${structure.organism}\n`;
                content += `📝 Description: ${structure.description.substring(0, 150)}...\n`;
                content += `🔗 **[View PDB Structure](${structure.url})**\n\n`;
            });
            
            content += `### 🎯 **Research Applications**\n`;
            content += `- Molecular docking studies with target proteins\n`;
            content += `- Structure-based drug design and optimization\n`;
            content += `- Functional analysis of protein-protein interactions\n`;
            content += `- Cryo-EM and X-ray crystallography validation\n\n`;
        }
        
        // FEATURE 3: PUBCHEM COMPOUND SUGGESTIONS  
        if (data.feature_3_pubchem) {
            const pubchem = data.feature_3_pubchem;
            content += `## 💊 FEATURE 3: PubChem Compound Database\n\n`;
            
            content += `### **${pubchem.query_context}**\n\n`;
            content += `📊 **${pubchem.compounds_found} drug compounds** identified from PubChem database\n\n`;
            
            content += `### 🧪 **Chemical Compound Library**\n`;
            pubchem.compounds.forEach((compound, index) => {
                content += `**${index + 1}. ${compound.name}** (CID: ${compound.cid})\n`;
                content += `🔬 Synonyms: ${compound.synonyms.slice(0, 3).join(', ')}\n`;
                content += `⚗️ Formula: ${compound.molecular_formula} | MW: ${compound.molecular_weight} Da\n`;
                content += `💊 Drug Info: ${compound.drug_info}\n`;
                content += `🎯 Mechanism: ${compound.mechanism}\n`;
                content += `🩺 Targets: ${compound.targets.slice(0, 2).join(', ')}\n`;
                content += `🦠 Indications: ${compound.indications.slice(0, 2).join(', ')}\n`;
                content += `🔗 **[PubChem Profile](${compound.url})**\n\n`;
            });
            
            content += `### 🎯 **Drug Discovery Applications**\n`;
            content += `- High-throughput screening compound libraries\n`;
            content += `- Lead optimization and SAR studies\n`;
            content += `- Drug-target interaction analysis\n`;
            content += `- ADMET property prediction and validation\n\n`;
        }
        
        // FEATURE 4: SMART VISUALIZATION PREVIEW
        if (data.feature_4_visualization) {
            const viz = data.feature_4_visualization;
            content += `## 🎨 FEATURE 4: Smart Visualization Preview\n\n`;
            
            content += `### **${viz.suggested_title}**\n\n`;
            content += `📊 **Visualization Type**: ${viz.visualization_type.replace('_', ' ').toUpperCase()}\n`;
            content += `🔍 **Context**: ${viz.query_context}\n\n`;
            
            content += `### 📈 **Data Sources for Visualization**\n`;
            content += `- **Literature**: ${viz.data_sources.literature_data} research papers\n`;
            content += `- **Protein Structures**: ${viz.data_sources.protein_structures} PDB structures\n`;
            content += `- **Drug Compounds**: ${viz.data_sources.drug_compounds} PubChem compounds\n\n`;
            
            content += `### ⬇️ **Interactive Preview Panel**\n`;
            content += `\`\`\`visualization\n`;
            content += `{\n`;
            content += `  "type": "${viz.visualization_type}",\n`;
            content += `  "title": "${viz.suggested_title}",\n`;
            content += `  "sources": {\n`;
            content += `    "literature": ${viz.data_sources.literature_data},\n`;
            content += `    "structures": ${viz.data_sources.protein_structures},\n`;
            content += `    "compounds": ${viz.data_sources.drug_compounds}\n`;
            content += `  },\n`;
            content += `  "formats": ${JSON.stringify(viz.download_formats)}\n`;
            content += `}\n`;
            content += `\`\`\`\n\n`;
            
            content += `### 💾 **Download Options**\n`;
            viz.download_formats.forEach(format => {
                content += `- **[Download ${format}](javascript:downloadVisualization('${viz.visualization_type}', '${format}'))** 📁\n`;
            });
            content += `\n`;
            
            content += `*🎨 Interactive visualization generated on-demand! Download in multiple formats.*\n\n`;
        }
        
        // Clean Summary section - NO TL;DR
        content += `## 📋 Summary\n\n`;
        if (data.pubmed_articles && data.pubmed_articles.length > 0) {
            content += `✅ **${data.pubmed_articles.length} research articles** analyzed with real citations and links\n`;
        }
        if (data.clinical_trials && data.clinical_trials.length > 0) {
            content += `✅ **${data.clinical_trials.length} clinical trials** identified with status and details\n`;
        }
        
        // Add MAX LEVEL summary
        if (data.max_level_features) {
            const maxLevel = data.max_level_features;
            if (maxLevel.molecular_targets?.pdb_structures?.length > 0) {
                content += `✅ **${maxLevel.molecular_targets.pdb_structures.length} PDB structures** for structural biology research\n`;
            }
            if (maxLevel.molecular_targets?.pubchem_compounds?.length > 0) {
                content += `✅ **${maxLevel.molecular_targets.pubchem_compounds.length} drug compounds** from PubChem database\n`;
            }
            if (maxLevel.research_workflow) {
                content += `✅ **Complete research workflow** with tools and timelines\n`;
            }
        }
        
        // DYNAMIC, RESPONSE-SPECIFIC SUMMARY (No more generic spam!)
        
        // Count actual features used
        let featuresUsed = 0;
        let featureDetails = [];
        
        if (data.feature_1_feedback) {
            featuresUsed++;
            featureDetails.push('AI-generated feedback mechanism analysis');
        }
        if (data.feature_2_pdb) {
            featuresUsed++;
            featureDetails.push(`protein structures (${data.feature_2_pdb.structures_found} PDB entries)`);
        }
        if (data.feature_3_pubchem) {
            featuresUsed++;
            featureDetails.push(`drug compounds (${data.feature_3_pubchem.compounds_found} PubChem entries)`);
        }
        if (data.feature_4_visualization) {
            featuresUsed++;
            featureDetails.push(`smart visualization (${data.feature_4_visualization.visualization_type} type)`);
        }
        
        // Generate response-specific summary
        content += `✅ **Research analysis** completed successfully\n`;
        
        if (featuresUsed > 0) {
            content += `✅ **Advanced features** utilized:\n`;
            featureDetails.forEach(feature => {
                content += `   - ${feature}\n`;
            });
        }
        
        content += `✅ **Analysis depth** based on ${data.pubmed_articles.length + data.clinical_trials.length} data sources\n\n`;
        
        // Add specific insights based on what was found
        if (data.pubmed_articles.length > 0) {
            content += `📚 **Key insight**: ${data.pubmed_articles.length} recent research articles provide comprehensive coverage of your query\n`;
        }
        if (data.clinical_trials.length > 0) {
            content += `🏥 **Clinical relevance**: ${data.clinical_trials.length} active clinical trials identified for practical applications\n`;
        }
        
        content += `\n*Comprehensive analysis generated with real citations and interactive features.*`;
        
        return content;
    } else {
        // Fallback for unknown types
        return `${data.response || "No response available"}`;
    }
    };

    const formatResponse = (data, mode) => {
        if (mode === 'literature') {
            // New structure: Answer + Links + Summary
            let content = `${data.rag_summary}\n\n`;
            
            // Literature Links & Citations
            if (data.pubmed_articles && data.pubmed_articles.length > 0) {
                content += `📚 **Literature & Citations**\n\n`;
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
                content += `🏥 **Clinical Trials (${data.clinical_trials.length})**\n`;
                data.clinical_trials.forEach((trial, index) => {
                    content += `${index + 1}. ${trial.title}\n`;
                    content += `   Status: ${trial.status}\n`;
                    if (trial.url) {
                        content += `   🔗 View Trial: ${trial.url}\n`;
                    }
                    content += `\n`;
                });
            }
            
            // Generate proper summary based on actual data
            let summaryPoints = [];
            if (data.pubmed_articles && data.pubmed_articles.length > 0) {
                summaryPoints.push(`${data.pubmed_articles.length} recent research articles analyzed`);
            }
            if (data.clinical_trials && data.clinical_trials.length > 0) {
                summaryPoints.push(`${data.clinical_trials.length} clinical trials identified`);
            }
            summaryPoints.push(`Evidence-based insights from current literature`);
            summaryPoints.push(`Comprehensive analysis of molecular mechanisms and therapeutic approaches`);
            
            content += `\n📋 **Summary**\n`;
            content += `Key findings: ${summaryPoints.join(' • ')}. This analysis is based on the latest peer-reviewed research and provides actionable insights for understanding current developments in this field.`;
            
            return content;
        } else if (mode === 'hypothesis') {
            let content = `## 🧬 ENHANCED HYPOTHESIS GENERATION\n\n`;
            content += `**Research Topic:** ${data.input}\n\n`;
            content += `${data.hypothesis}\n\n`;
            
            content += `## 📊 RESEARCH QUALITY METRICS\n\n`;
            content += `🔬 **Plausibility Score:** ${(data.plausibility_score * 100).toFixed(1)}%\n`;
            content += `🎯 **Confidence Level:** ${data.confidence}\n`;
            content += `📚 **Literature Context:** ${data.research_context || 'Analysis based on literature'}\n`;
            content += `🏥 **Clinical Trials:** ${data.trials_count || 0} studies\n\n`;
            
            content += `## 📚 SUPPORTING LITERATURE (${data.literature_count || 0} articles)\n\n`;
            if (data.citations && data.citations.length > 0) {
                data.citations.forEach((citation, index) => {
                    content += `**${index + 1}. ${citation.title}**\n`;
                    content += `   Authors: ${citation.authors || 'N/A'}\n`;
                    content += `   Journal: ${citation.journal || 'N/A'}\n`;
                    if (citation.url) {
                        content += `   🔗 **[Read Full Article](${citation.url})**\n`;
                    }
                    content += `\n`;
                });
            }
            
            if (data.clinical_trials && data.clinical_trials.length > 0) {
                content += `## 🏥 CLINICAL TRIALS (${data.clinical_trials.length})\n\n`;
                data.clinical_trials.forEach((trial, index) => {
                    content += `**${index + 1}. ${trial.title}**\n`;
                    content += `   Status: ${trial.status} | Phase: ${trial.phase}\n`;
                    content += `\n`;
                });
            }
            
            content += `## 🔗 RESEARCH DATA SOURCES\n\n`;
            content += `${data.sponsor_tech}\n\n`;
            content += `---\n`;
            content += `**Hypothesis Type:** ${data.hypothesis_type || 'Evidence-based biomedical research'}`;
            return content;
        } else if (mode === 'download') {
            let content = `# 📥 Data Download Center\n\n`;
            content += `**Compound:** ${data.pubchem_data?.name || data.compound_name}\n`;
            content += `**Formula:** ${data.pubchem_data?.molecular_formula || 'N/A'}\n`;
            content += `**Molecular Weight:** ${data.pubchem_data?.molecular_weight || 'N/A'} Da\n\n`;
            
            content += `## 📊 Available Data\n\n`;
            content += `🧪 **Compounds:** ${data.data_summary.compounds_found}\n`;
            content += `🏗️ **Protein Structures:** ${data.data_summary.structures_found}\n`;
            content += `📚 **Research Articles:** ${data.data_summary.articles_found}\n`;
            content += `🔬 **Clinical Trials:** ${data.data_summary.trials_found}\n\n`;
            
            content += `## 🔗 Download Links\n\n`;
            
            // Group links by category for clean organization
            const compoundLinks = [];
            const structureLinks = [];
            const researchLinks = [];
            
            Object.entries(data.download_links).forEach(([key, url]) => {
                if (url && url.trim()) {
                    const linkEntry = { 
                        key, 
                        url, 
                        label: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) 
                    };
                    
                    if (key.includes('pubchem') || key.includes('compound')) {
                        compoundLinks.push(linkEntry);
                    } else if (key.includes('pdb') || key.includes('structure')) {
                        structureLinks.push(linkEntry);
                    } else {
                        researchLinks.push(linkEntry);
                    }
                }
            });
            
            if (compoundLinks.length > 0) {
                content += `### 💊 Compound Data\n`;
                compoundLinks.forEach(({ label, url }) => {
                    content += `• **${label}**: [${url}](${url})\n`;
                });
                content += `\n`;
            }
            
            if (structureLinks.length > 0) {
                content += `### 🧬 Protein Structures\n`;
                structureLinks.forEach(({ label, url }) => {
                    content += `• **${label}**: [${url}](${url})\n`;
                });
                content += `\n`;
            }
            
            if (researchLinks.length > 0) {
                content += `### 📚 Research Databases\n`;
                researchLinks.forEach(({ label, url }) => {
                    content += `• **${label}**: [${url}](${url})\n`;
                });
                content += `\n`;
            }
            
            content += `---\n`;
            content += `*Powered by PubChem, PDB, PubMed & ClinicalTrials.gov APIs*`;
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

    // Function to save current chat to history
    const saveCurrentChatToHistory = async () => {
        if (messages.length > 0 && currentSessionId) {
            try {
                const token = localStorage.getItem('token');
                
                // Check if token exists
                if (!token) {
                    console.error('❌ No authentication token found for saving chat');
                    return;
                }
                
                // Extract context from all messages to generate smart title
                const allContent = messages.map(m => m.content).join(' ');
                const diseases = allContent.match(/\b(diabetes|cancer|alzheimer|parkinson|heart disease|stroke|covid|influenza|hepatitis|HIV|AIDS|leukemia|lymphoma|melanoma)\b/gi) || [];
                const drugs = allContent.match(/\b(insulin|metformin|aspirin|warfarin|caffeine|morphine|paracetamol|ibuprofen|chemotherapy|immunotherapy)\b/gi) || [];
                const proteins = allContent.match(/\b([A-Z]{2,4}\d+|protein|enzyme|receptor|antibody)\b/g) || [];
                const topics = allContent.match(/\b(treatment|therapy|diagnosis|mechanism|pathway|clinical trial|research)\b/gi) || [];
                
                // Generate smart title based on content
                let title = 'Research Session';
                if (diseases.length > 0) {
                    title = `${diseases[0]} Research`;
                } else if (drugs.length > 0) {
                    title = `${drugs[0]} Analysis`;
                } else if (proteins.length > 0) {
                    title = `${proteins[0]} Study`;
                } else if (topics.length > 0) {
                    title = `${topics[0]} Discussion`;
                } else {
                    // Check for casual conversations
                    const firstUserMessage = messages.find(msg => msg.role === 'user');
                    if (firstUserMessage) {
                        const firstMessage = firstUserMessage.content.toLowerCase().trim();
                        
                        // Handle casual greetings and conversations
                        if (/^(hi|hello|hey|good morning|good afternoon|good evening|greetings)$/.test(firstMessage)) {
                            title = `Chat - ${new Date().toLocaleDateString()}`;
                        } else if (/^(thanks|thank you|bye|goodbye|see you)$/.test(firstMessage)) {
                            title = `Conversation - ${new Date().toLocaleDateString()}`;
                        } else if (firstMessage.length <= 20) {
                            // Short messages get a generic title with date
                            title = `Quick Chat - ${new Date().toLocaleDateString()}`;
                        } else {
                            // Longer messages use the actual content
                            title = firstUserMessage.content.substring(0, 40) + (firstUserMessage.content.length > 40 ? '...' : '');
                        }
                    }
                }
                
                // Ensure title is always a string
                const safeTitle = title || `Chat - ${new Date().toLocaleDateString()}`;
                
                // Update the current session title
                const description = (safeTitle.includes('Research') || safeTitle.includes('Analysis') || safeTitle.includes('Study'))
                    ? `Research session with ${messages.length} messages`
                    : `Chat conversation with ${messages.length} messages`;
                    
                try {
                    await axios.patch(`${API_URL}/api/chat/sessions/${currentSessionId}`, {
                        title: safeTitle,
                        description: description
                    }, {
                        headers: { Authorization: `Bearer ${token}` }
                    });
                    console.log('✅ Session title updated successfully');
                } catch (patchError) {
                    console.warn('Could not update session title:', patchError);
                    if (patchError.response?.status === 401) {
                        console.error('❌ Authentication failed during title update');
                        return;
                    }
                }
                
                // Refresh chat sessions to show updated title
                try {
                    await loadChatSessions();
                    console.log('✅ Current chat saved to history with title:', safeTitle);
                } catch (loadError) {
                    console.warn('Could not refresh chat sessions:', loadError);
                }
            } catch (error) {
                console.error('Error saving chat to history:', error);
                if (error.response?.status === 401) {
                    console.error('❌ Authentication failed during chat save');
                    setError('Your session has expired. Please log in again.');
                    handleLogout();
                }
            }
        }
    };

    // Expose functions to components
    useEffect(() => {
        window.createNewChatSession = createNewChatSession;
        window.clearMessages = () => setMessages([]);
        window.loadChatSession = loadChatSessions;
        window.switchToSession = switchToSession;
        window.chatSessions = chatSessions;
        window.messages = messages;
        window.saveCurrentChatToHistory = saveCurrentChatToHistory;
        window.setActiveMode = setActiveMode;
        window.handleFileSelect = (file) => {
            setSelectedFile(file);
        };
        
        // 🆕 NEW TEAM WORKSPACE MODAL FUNCTION
        window.openTeamWorkspace = () => {
            console.log('🔄 openTeamWorkspace called, opening new modal');
            setShowTeamWorkspaceModal(true);
        };
    }, [chatSessions, createNewChatSession, loadChatSessions, switchToSession, messages]);

    const getModeIcon = (mode) => {
        switch (mode) {
            case 'chat': return '💬';
            case 'literature': return '🟢';
            case 'hypothesis': return '🔵';
            case 'download': return '🟠';
            default: return '⚪';
        }
    };

    const getModeLabel = (mode) => {
        switch (mode) {
            case 'chat': return 'Smart Chat';
            case 'literature': return 'Search Literature';
            case 'hypothesis': return 'Generate Hypothesis';
            case 'download': return 'Download Data';
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

    // Function to format and enhance content with improved structure
    const formatContent = (content) => {
        // Safety check for undefined content
        if (!content || typeof content !== 'string') {
            return '<p class="text-white/70 italic">Response content unavailable</p>';
        }
        
        let formatted = content;
        
        // STEP 1: Convert markdown links to HTML FIRST (before any other formatting)
        // Match **[text](url)** or [text](url)** or [text](url) patterns
        formatted = formatted.replace(/\*\*\[([^\]]+)\]\(([^)]+)\)\*\*/g, (match, text, url) => {
            return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:text-blue-300 underline font-medium">${text}</a>`;
        });
        formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)\**/g, (match, text, url) => {
            return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:text-blue-300 underline font-medium">${text}</a>`;
        });
        formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, url) => {
            return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:text-blue-300 underline font-medium">${text}</a>`;
        });
        
        // STEP 2: Make plain URLs clickable
        formatted = linkifyText(formatted);
        
        // STEP 3: Format TL;DR section with special styling
        formatted = formatted.replace(
            /\*\*TL;DR:\*\*\s*(.*?)(\n|$)/gi,
            '<div class="tldr-section mt-6 mb-4 p-4 bg-gradient-to-r from-blue-600 to-blue-500 rounded-lg border-l-4 border-blue-400 shadow-lg">' +
            '<strong class="text-white font-bold text-base block mb-2">📌 TL;DR (Too Long; Didn\'t Read)</strong>' +
            '<p class="text-white text-sm leading-relaxed">$1</p>' +
            '</div>'
        );
        
        // STEP 4: Format main headings (##)
        formatted = formatted.replace(/^##\s+(.+)$/gm, '<h2 class="text-xl font-bold text-blue-300 mt-6 mb-3 border-b border-blue-600 pb-2">$1</h2>');
        
        // STEP 5: Format subheadings (###)
        formatted = formatted.replace(/^###\s+(.+)$/gm, '<h3 class="text-lg font-semibold text-blue-200 mt-4 mb-2">$1</h3>');
        
        // STEP 6: Format bold text with better styling (but not in already-converted links)
        formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong class="text-blue-300 font-semibold">$1</strong>');
        
        // STEP 7: Format bullet points with better styling
        formatted = formatted.replace(/^[•\-]\s+(.+)$/gm, '<li class="ml-4 mb-2 text-gray-200">$1</li>');
        
        // STEP 8: Wrap consecutive list items in ul with better styling
        formatted = formatted.replace(/(<li.*?<\/li>\s*)+/g, '<ul class="list-disc ml-6 my-3 space-y-1">$&</ul>');
        
        // STEP 9: Format numbered lists with better styling
        formatted = formatted.replace(/^(\d+)\.\s+(.+)$/gm, '<div class="ml-4 mb-2 flex"><span class="text-blue-400 font-semibold mr-2 min-w-[2rem]">$1.</span><span class="text-gray-200">$2</span></div>');
        
        // STEP 10: Format code blocks
        formatted = formatted.replace(/`([^`]+)`/g, '<code class="bg-gray-700 text-green-400 px-2 py-1 rounded text-sm font-mono">$1</code>');
        
        // STEP 11: Add proper paragraph spacing with better styling
        formatted = formatted.replace(/\n\n/g, '</p><p class="mt-3 mb-3 text-gray-200 leading-relaxed">');
        formatted = '<p class="mt-3 mb-3 text-gray-200 leading-relaxed">' + formatted + '</p>';
        
        return formatted;
    };

    // Function to render message content with enhanced formatting
    const renderMessageContent = (content) => {
        const formattedContent = formatContent(content);
        return <div className="message-content" dangerouslySetInnerHTML={{ __html: formattedContent }} />;
    };

    // Show login screen if user is not authenticated
    if (!user) {
        return <DynamicLogin onLogin={(userData, token) => {
            setUser(userData);
            // Save user data to localStorage for session persistence
            localStorage.setItem('user', JSON.stringify(userData));
            // Use the real JWT token from backend login
            if (token) {
                localStorage.setItem('token', token);
            }
            // Start at homepage after login
            setCurrentPage('homepage');
            localStorage.setItem('currentPage', 'homepage');
        }} />;
    }

    // Show Homepage (Landing page after login)
    if (currentPage === 'homepage') {
        return <Homepage user={user} onNavigate={handleNavigate} onLogout={handleLogout} />;
    }

    // Show 3D Molecule Viewer
    if (currentPage === 'molecule-viewer') {
        const backTo = previousPage === 'chat' ? 'chat' : 'homepage';
        const backLabel = previousPage === 'chat' ? 'Back to Chat' : 'Back to Home';
            return <Fixed3DViewer onBack={() => setCurrentPage(backTo)} backLabel={backLabel} />;
    }
    
    // Show About page
    if (currentPage === 'about') {
        return (
            <div className="min-h-screen bg-clintra-navy text-white p-16">
                <div className="max-w-4xl mx-auto">
                    <button 
                        onClick={() => setCurrentPage('homepage')}
                        className="mb-8 text-clintra-cyan hover:text-clintra-teal transition-colors"
                    >
                        ← Back to Home
                    </button>
                    <h1 className="text-5xl font-bold text-clintra-cyan mb-8">About Clintra</h1>
                    <p className="text-xl text-white/80 leading-relaxed">
                        Clintra is an AI-powered drug discovery platform that accelerates biomedical research 
                        by providing instant access to literature, generating research hypotheses, and 
                        visualizing molecular structures. Built with cutting-edge AI technology including 
                        Cerebras Llama, OpenAI, and comprehensive biomedical databases.
                    </p>
                </div>
            </div>
        );
    }
    
    // Show NEW Chat Page with 3-section layout
    if (currentPage === 'chat') {
        return (
            <ChatPage 
                user={user}
                messages={messages}
                activeMode={activeMode}
                onModeChange={handleModeChange}
                onBack={() => setCurrentPage('homepage')}
                onLogout={handleLogout}
                onNavigate={handleNavigate}
                onSendMessage={handleSendMessage}
                inputValue={inputValue}
                setInputValue={setInputValue}
                isLoading={isLoading}
            />
        );
    }

    // Get mode-specific theme colors
    const getModeTheme = () => {
        switch(activeMode) {
            case 'literature':
                return {
                    bg: 'bg-gradient-to-br from-clintra-navy via-clintra-navy-light to-clintra-teal/10',
                    accent: 'clintra-cyan',
                    glow: 'glow-literature'
                };
            case 'hypothesis':
                return {
                    bg: 'bg-gradient-to-br from-clintra-navy via-clintra-navy-light to-clintra-purple/10',
                    accent: 'clintra-purple',
                    glow: 'glow-hypothesis'
                };
            case 'download':
                return {
                    bg: 'bg-gradient-to-br from-clintra-navy via-clintra-navy-light to-clintra-gold/10',
                    accent: 'clintra-gold',
                    glow: 'glow-download'
                };
            default:
                return {
                    bg: 'bg-clintra-navy',
                    accent: 'clintra-cyan',
                    glow: ''
                };
        }
    };

    const modeTheme = getModeTheme();

    return (
        <>
        <div className={`min-h-screen ${modeTheme.bg} flex transition-all duration-500`}>
            {/* Sidebar - Dark Navy Theme */}
            <div className={`${sidebarOpen ? 'w-64' : 'w-0'} transition-all duration-300 bg-clintra-navy-dark shadow-2xl overflow-hidden border-r border-clintra-teal/20`}>
                <div className="p-4">
                    <div className="flex items-center mb-6">
                        <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3">
                            <span className="text-white font-bold text-sm">C</span>
                        </div>
                        <h2 className="text-lg font-semibold text-white">Clintra</h2>
                    </div>
                        <nav className="space-y-1">
                            {/* Home Button */}
                            <button
                                onClick={() => setCurrentPage('homepage')}
                                className="w-full text-left p-3 rounded-lg hover:bg-clintra-teal/20 flex items-center text-clintra-cyan hover:text-white transition-colors border border-clintra-teal/30"
                            >
                                <span className="mr-3 text-lg">🏠</span>
                                Home
                            </button>
                            
                            <button
                                onClick={createNewChat}
                                className="w-full text-left p-3 rounded-lg hover:bg-gray-700 flex items-center text-gray-300 hover:text-white transition-colors"
                            >
                                <span className="mr-3 text-lg">💬</span>
                                New Chat
                            </button>
                            
                            {/* 🔥 TEAM COLLABORATION BUTTONS */}
                            <button
                                onClick={() => setShowWorkspaceModal(true)}
                                className="w-full text-left p-3 rounded-lg hover:bg-gray-700 flex items-center text-gray-300 hover:text-white transition-colors"
                            >
                                <span className="mr-3 text-lg">👥</span>
                                Manage Teams
                            </button>
                            
                            {/* 🔬 3D MOLECULE VIEWER BUTTON */}
                            <button
                                onClick={() => setCurrentPage('molecule-viewer')}
                                className={`w-full text-left p-3 rounded-lg hover:bg-gray-700 flex items-center transition-colors ${
                                    currentPage === 'molecule-viewer' 
                                        ? 'bg-blue-600 text-white' 
                                        : 'text-gray-300 hover:text-white'
                                }`}
                            >
                                <span className="mr-3 text-lg">🔬</span>
                                3D Molecule Viewer
                            </button>
                            
                            {/* 🔄 BACK TO CHAT BUTTON (when on molecule viewer) */}
                            {currentPage === 'molecule-viewer' && (
                                <button
                                    onClick={() => setCurrentPage('chat')}
                                    className="w-full text-left p-3 rounded-lg bg-green-600 hover:bg-green-700 flex items-center text-white transition-colors mt-2"
                                >
                                    <span className="mr-3 text-lg">💬</span>
                                    Back to Chat
                                </button>
                            )}
                            
                            <div className="border-t border-gray-700 my-4"></div>
                            
                            <div className="text-xs text-gray-400 uppercase tracking-wide mb-2 px-3">
                                Recent Chats
                            </div>
                            
                            {chatSessions.slice(0, 5).map((session) => (
                                <button
                                    key={session.id}
                                    onClick={async () => {
                                        await switchToSession(session.id);
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
                {/* 🎨 NAVBAR - Like Homepage */}
                <header className="bg-clintra-navy-light border-b border-clintra-teal/20 px-6 py-4">
                    <div className="flex items-center justify-between">
                        {/* Left: Logo + CLINTRA Name */}
                        <div className="flex items-center space-x-3">
                            <button
                                onClick={() => setSidebarOpen(!sidebarOpen)}
                                className="p-2 rounded-lg hover:bg-clintra-teal/20 text-clintra-cyan transition-colors mr-2"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                </svg>
                            </button>
                            
                            <div className="w-10 h-10 bg-gradient-to-br from-clintra-teal to-clintra-cyan rounded-xl flex items-center justify-center glow-teal">
                                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                                </svg>
                            </div>
                            <h1 className="text-2xl font-black text-clintra-cyan tracking-tight">CLINTRA</h1>
                        </div>
                        
                        {/* Right: Online Status + Username + Profile Menu */}
                        <div className="flex items-center space-x-6">
                            {/* Online Status */}
                            <div className="flex items-center space-x-2">
                                <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-400' : 'bg-red-400'} animate-pulse`}></div>
                                <span className="text-sm text-white/80">
                                    {isOnline ? 'Online' : 'Offline'}
                                </span>
                            </div>
                            
                            {/* Username */}
                            <div className="text-white font-medium">
                                {user.full_name || user.username}
                            </div>
                            
                            {/* Profile Button with Dropdown */}
                            <div className="relative">
                                <button 
                                    onClick={() => setShowProfileMenu(!showProfileMenu)}
                                    className="w-10 h-10 bg-gradient-to-br from-clintra-teal to-clintra-cyan rounded-full flex items-center justify-center hover:shadow-lg transition-all glow-teal"
                                >
                                    <span className="text-white font-bold text-sm">
                                        {(user.full_name || user.username).charAt(0).toUpperCase()}
                                    </span>
                                </button>
                                
                                {/* Dropdown Menu */}
                                {showProfileMenu && (
                                    <div className="absolute right-0 mt-2 w-56 bg-clintra-navy-lighter border border-clintra-teal/30 rounded-xl shadow-2xl py-2 z-50">
                                        <button
                                            onClick={() => {/* Account settings */}}
                                            className="w-full text-left px-4 py-3 hover:bg-clintra-teal/10 text-white transition-colors flex items-center space-x-3"
                                        >
                                            <svg className="w-5 h-5 text-clintra-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                            </svg>
                                            <span>Account Settings</span>
                                        </button>
                                        
                                        <ExportImport messages={messages} onImport={handleImportMessages} />
                                        
                                        <button
                                            onClick={() => setShowSearch(true)}
                                            className="w-full text-left px-4 py-3 hover:bg-clintra-teal/10 text-white transition-colors flex items-center space-x-3"
                                        >
                                            <svg className="w-5 h-5 text-clintra-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                            </svg>
                                            <span>Search Messages</span>
                                        </button>
                                        
                                        <div className="border-t border-clintra-teal/20 my-2"></div>
                                        
                                        <button
                                            onClick={handleLogout}
                                            className="w-full text-left px-4 py-3 hover:bg-red-500/10 text-red-400 transition-colors flex items-center space-x-3"
                                        >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                                            </svg>
                                            <span>Logout</span>
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
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
                                
                                {/* Message Content - Transparent Floating */}
                                <div
                                    className={`p-6 rounded-2xl backdrop-blur-xl transition-all shadow-2xl ${
                                        message.role === 'user'
                                            ? 'bg-clintra-teal/10 border border-clintra-teal/30 hover:border-clintra-cyan/50 text-white'
                                            : 'glass-morphism-strong hover:border-clintra-cyan/30 text-gray-100'
                                    }`}
                                >
                                    {/* File Analysis Message */}
                                    {message.type === 'file_analysis' ? (
                                        <div className="space-y-4">
                                            {/* File Info Header */}
                                            <div className="flex items-center space-x-3 pb-3 border-b border-gray-600">
                                                <div className="flex-shrink-0">
                                                    {message.file_info?.type?.startsWith('image/') ? (
                                                        <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                                        </svg>
                                                    ) : message.file_info?.type === 'application/pdf' ? (
                                                        <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                                        </svg>
                                                    ) : (
                                                        <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                                        </svg>
                                                    )}
                                                </div>
                                                <div>
                                                    <h3 className="font-semibold text-white">📎 File Analysis</h3>
                                                    <p className="text-sm text-gray-400">
                                                        {message.file_info?.name} • {(message.file_info?.size / 1024 / 1024)?.toFixed(2)} MB
                                                    </p>
                                                </div>
                                            </div>
                                            
                                            {/* Query Context */}
                                            {message.query && message.query !== 'File analysis' && (
                                                <div className="bg-gray-700 rounded-lg p-3">
                                                    <p className="text-sm text-gray-300">
                                                        <span className="font-medium text-blue-400">Query:</span> {message.query}
                                                    </p>
                            </div>
                        )}
                                            
                                            {/* Analysis Content */}
                                            <div className="message-content">{renderMessageContent(message.analysis)}</div>
                                            
                                            {/* AI Models Used */}
                                            <div className="mt-4 pt-3 border-t border-gray-600">
                                                <div className="flex flex-wrap gap-2 text-xs">
                                                    {message.primary_ai && (
                                                        <span className="px-2 py-1 bg-blue-600 text-white rounded-full">
                                                            🎯 {message.primary_ai}
                                                        </span>
                                                    )}
                                                    {message.enhancement_ai && (
                                                        <span className="px-2 py-1 bg-purple-600 text-white rounded-full">
                                                            🏆 {message.enhancement_ai}
                                                        </span>
                                                    )}
                                                </div>
                                                {message.sponsor_tech && (
                                                    <p className="text-xs text-gray-400 mt-2">{message.sponsor_tech}</p>
                                                )}
                                            </div>
                                        </div>
                                    ) : (
                                        /* Regular Message */
                                        <div>
                                            <div className="message-content">{renderMessageContent(message.content)}</div>
                                            {message.mode && (
                                                <div className="mt-2 text-xs text-gray-400">
                                                    Mode: {getModeLabel(message.mode)}
                                                </div>
                                            )}
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

                {/* Message Search Modal */}
                {showSearch && (
                    <MessageSearch
                        messages={messages}
                        onSearch={handleSearchMessage}
                        onClose={() => setShowSearch(false)}
                    />
                )}

                {/* Input Area */}
                <div className="bg-gray-800 border-t border-gray-700 p-4">
                    {/* Quick Action Buttons */}
                    <div className="flex space-x-2 mb-4">
                        <button
                            onClick={() => handleModeChange('literature')}
                            className={`px-6 py-3 rounded-xl text-sm font-semibold transition-all transform hover:scale-105 ${
                                activeMode === 'literature'
                                    ? 'bg-gradient-to-r from-clintra-teal to-clintra-cyan text-white shadow-2xl glow-literature border border-clintra-cyan/50'
                                    : 'bg-clintra-navy-lighter border border-clintra-teal/30 text-clintra-teal hover:bg-clintra-teal/10 hover:border-clintra-teal'
                            }`}
                        >
                            🔍 Literature Search
                        </button>
                        <button
                            onClick={() => handleModeChange('hypothesis')}
                            className={`px-6 py-3 rounded-xl text-sm font-semibold transition-all transform hover:scale-105 ${
                                activeMode === 'hypothesis'
                                    ? 'bg-gradient-to-r from-clintra-purple-dark to-clintra-purple text-white shadow-2xl glow-hypothesis border border-clintra-purple/50'
                                    : 'bg-clintra-navy-lighter border border-clintra-purple/30 text-clintra-purple hover:bg-clintra-purple/10 hover:border-clintra-purple'
                            }`}
                        >
                            🧬 Hypothesis Generation
                        </button>
                        <button
                            onClick={() => handleModeChange('download')}
                            className={`px-6 py-3 rounded-xl text-sm font-semibold transition-all transform hover:scale-105 ${
                                activeMode === 'download'
                                    ? 'bg-gradient-to-r from-clintra-gold-dark to-clintra-gold text-white shadow-2xl glow-download border border-clintra-gold/50'
                                    : 'bg-clintra-navy-lighter border border-clintra-gold/30 text-clintra-gold hover:bg-clintra-gold/10 hover:border-clintra-gold'
                            }`}
                        >
                            📥 Download Data
                        </button>
                        
                        {/* 🔥 SHARE RESEARCH BUTTON */}
                        {user && currentWorkspace && (
                            <button
                                onClick={() => {
                                    const latestContent = messages.length > 0 
                                        ? messages[messages.length - 1].content 
                                        : 'No research content to share';
                                    setSelectedContentForShare(latestContent);
                                    setShowShareModal(true);
                                }}
                                className="px-4 py-2 rounded-lg text-sm font-medium bg-orange-600 text-white hover:bg-orange-700 transition-all shadow-lg"
                            >
                                🔗 Share Research
                            </button>
                        )}
                        </div>

                    {/* Search Input */}
                    <form onSubmit={handleSendMessage} className="space-y-3">
                        {/* File Attachment Section */}
                        {selectedFile && (
                            <div className="bg-gray-700 rounded-lg p-3 border border-gray-600">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-3">
                                        <div className="flex-shrink-0">
                                            {selectedFile.type.startsWith('image/') ? (
                                                <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                                </svg>
                                            ) : selectedFile.type === 'application/pdf' ? (
                                                <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                                </svg>
                                            ) : (
                                                <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                                </svg>
                                            )}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium text-white truncate">{selectedFile.name}</p>
                                            <p className="text-xs text-gray-400">
                                                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB • 
                                                {selectedFile.type.startsWith('image/') ? ' Image Analysis' : 
                                                 selectedFile.type === 'application/pdf' ? ' PDF Analysis' : ' Document Analysis'}
                                            </p>
                                        </div>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={handleRemoveFile}
                                        className="flex-shrink-0 p-1 text-gray-400 hover:text-red-400 transition-colors"
                                    >
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                            </button>
                                </div>
                            </div>
                        )}
                        
                        <div className="flex space-x-3">
                            <div className="flex-1 relative">
                            <input
                                type="text"
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    placeholder={selectedFile 
                                        ? "Optional: Add context or questions about your file..."
                                        : !isOnline 
                                            ? "You're offline. Please check your connection."
                                            : activeMode === 'literature'
                                                ? "Ask me anything! I can chat or help with research..."
                                                : `Ask me about a disease, protein, or drug... (${getModeLabel(activeMode)} mode)`
                                    }
                                    className="w-full p-4 bg-gray-700 text-white placeholder-gray-400 rounded-xl border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all disabled:opacity-50"
                                    disabled={isLoading || isAnalyzingFile || !isOnline}
                                />
                                
                                {/* File Upload Button */}
                                <button
                                    type="button"
                                    onClick={() => fileInputRef.current?.click()}
                                    className="absolute right-3 top-1/2 transform -translate-y-1/2 p-2 text-gray-400 hover:text-blue-400 transition-colors"
                                    disabled={isLoading || isAnalyzingFile || !isOnline}
                                >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                                    </svg>
                            </button>
                                
                                {/* Hidden File Input */}
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    onChange={handleFileSelect}
                                    accept="image/*,.pdf,.doc,.docx"
                                    className="hidden"
                                />
                            </div>
                        <button
                            type="submit"
                            disabled={isLoading || isAnalyzingFile || (!inputValue.trim() && !selectedFile) || !isOnline}
                            className="px-6 py-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
                        >
                            {isAnalyzingFile ? (
                                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                            ) : selectedFile ? (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                                </svg>
                            ) : (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                </svg>
                            )}
                        </button>
                        </div>
                        </form>
                    </div>
                </div>
            </div>
        
        {/* 🔥 SHARE RESEARCH MODAL */}
        {showShareModal && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                    <h3 className="text-lg font-semibold mb-4">🔗 Share Research</h3>
                    <p className="text-gray-600 mb-4">Select workspace to share your research:</p>
                    
                    {workspaces.map(workspace => (
                        <div key={workspace.id} className="flex items-center justify-between p-3 border rounded-lg mb-2">
                            <div>
                                <h4 className="font-medium">{workspace.name}</h4>
                                <p className="text-sm text-gray-500">{workspace.description}</p>
                            </div>
                            <button
                                onClick={() => shareResearch(selectedContentForShare, workspace.id)}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                            >
                                Share
                            </button>
                                </div>
                            ))}
                    
                    <button
                        onClick={() => setShowShareModal(false)}
                        className="w-full mt-4 px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
                    >
                        Cancel
                    </button>
                </div>
            </div>
        )}
        
        {/* 🆕 NEW TEAM WORKSPACE MODAL */}
        <TeamWorkspaceModal 
            isOpen={showTeamWorkspaceModal}
            onClose={() => setShowTeamWorkspaceModal(false)}
            user={user}
        />
        </>
    );
}

export default App;