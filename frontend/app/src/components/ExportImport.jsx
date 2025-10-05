import React, { useState } from 'react';

const ExportImport = ({ messages, onImport }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [importError, setImportError] = useState('');

    const exportChatHistory = () => {
        const data = {
            exportDate: new Date().toISOString(),
            version: '1.0',
            messages: messages.map(msg => ({
                role: msg.role,
                content: msg.content,
                timestamp: msg.timestamp,
                mode: msg.mode
            }))
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `clintra-chat-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        setIsOpen(false);
    };

    const handleFileImport = (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                
                // Validate the data structure
                if (!data.messages || !Array.isArray(data.messages)) {
                    throw new Error('Invalid file format: missing messages array');
                }

                // Validate each message
                const validMessages = data.messages.filter(msg => 
                    msg.role && msg.content && msg.timestamp
                );

                if (validMessages.length === 0) {
                    throw new Error('No valid messages found in file');
                }

                onImport(validMessages);
                setImportError('');
                setIsOpen(false);
                
                // Reset file input
                event.target.value = '';
            } catch (error) {
                setImportError(`Import failed: ${error.message}`);
            }
        };
        reader.readAsText(file);
    };

    if (!isOpen) {
        return (
            <button
                onClick={() => setIsOpen(true)}
                className="p-2 rounded-lg hover:bg-gray-700 text-gray-300 hover:text-white transition-colors"
                title="Export/Import chat history"
            >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                </svg>
            </button>
        );
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white">Export/Import Chat</h3>
                    <button
                        onClick={() => setIsOpen(false)}
                        className="text-gray-400 hover:text-white transition-colors"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div className="space-y-4">
                    <div>
                        <h4 className="text-sm font-medium text-gray-300 mb-2">Export Chat History</h4>
                        <button
                            onClick={exportChatHistory}
                            className="w-full p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center"
                        >
                            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Export to JSON
                        </button>
                    </div>

                    <div>
                        <h4 className="text-sm font-medium text-gray-300 mb-2">Import Chat History</h4>
                        <input
                            type="file"
                            accept=".json"
                            onChange={handleFileImport}
                            className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                        {importError && (
                            <div className="mt-2 text-sm text-red-400">{importError}</div>
                        )}
                    </div>

                    <div className="text-xs text-gray-400">
                        <p>• Export creates a JSON file with all chat messages</p>
                        <p>• Import loads messages from a previously exported file</p>
                        <p>• Imported messages will be added to your current chat</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ExportImport;

