import React, { useState, useMemo } from 'react';

const MessageSearch = ({ messages, onSearch, onClose }) => {
    const [query, setQuery] = useState('');
    const [isOpen, setIsOpen] = useState(true);

    const filteredMessages = useMemo(() => {
        if (!query.trim()) return [];
        
        return messages.filter(msg => 
            msg.content.toLowerCase().includes(query.toLowerCase()) &&
            msg.role === 'assistant' // Only search assistant messages
        );
    }, [messages, query]);

    const handleSearch = (message) => {
        onSearch(message);
        setIsOpen(false);
        onClose();
    };

    const handleClose = () => {
        setIsOpen(false);
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-hidden">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white">Search Messages</h3>
                    <button
                        onClick={handleClose}
                        className="text-gray-400 hover:text-white transition-colors"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div className="mb-4">
                    <input
                        type="text"
                        placeholder="Search in messages..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        className="w-full p-3 bg-gray-700 text-white placeholder-gray-400 rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        autoFocus
                    />
                </div>

                <div className="overflow-y-auto max-h-96">
                    {query.trim() && (
                        <div className="mb-2 text-sm text-gray-400">
                            {filteredMessages.length} result{filteredMessages.length !== 1 ? 's' : ''} found
                        </div>
                    )}

                    {filteredMessages.length > 0 ? (
                        <div className="space-y-2">
                            {filteredMessages.map((message) => (
                                <div
                                    key={message.id}
                                    onClick={() => handleSearch(message)}
                                    className="p-3 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-600 transition-colors"
                                >
                                    <div className="text-sm text-gray-300 mb-1">
                                        {new Date(message.timestamp).toLocaleString()}
                                    </div>
                                    <div className="text-white text-sm line-clamp-3">
                                        {message.content.substring(0, 200)}
                                        {message.content.length > 200 && '...'}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : query.trim() ? (
                        <div className="text-center text-gray-400 py-8">
                            No messages found matching "{query}"
                        </div>
                    ) : (
                        <div className="text-center text-gray-400 py-8">
                            Start typing to search messages...
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MessageSearch;

