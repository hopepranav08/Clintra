import React, { useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
    const [health, setHealth] = useState(null);
    const [searchResults, setSearchResults] = useState([]);
    const [hypothesis, setHypothesis] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [hypothesisInput, setHypothesisInput] = useState('');

    const checkHealth = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/health`);
            setHealth(response.data);
        } catch (error) {
            setHealth({ status: 'error', database: 'disconnected' });
        }
    };

    const handleSearch = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.get(`${API_URL}/api/search`, { params: { query: searchQuery } });
            setSearchResults(response.data.results);
        } catch (error) {
            console.error("Search failed:", error);
            setSearchResults([]);
        }
    };

    const generateHypothesis = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post(`${API_URL}/api/hypothesis`, { text: hypothesisInput });
            setHypothesis(response.data.hypothesis);
        } catch (error) {
            console.error("Hypothesis generation failed:", error);
            setHypothesis('Failed to generate hypothesis.');
        }
    };

    return (
        <div className="min-h-screen bg-gray-100 text-gray-800">
            <header className="bg-white shadow p-4">
                <h1 className="text-3xl font-bold text-center text-blue-600">Clintra - AI Drug Discovery Assistant</h1>
            </header>
            <main className="p-8">
                <div className="max-w-4xl mx-auto">
                    {/* Health Check */}
                    <section className="mb-8 p-4 bg-white rounded shadow">
                        <h2 className="text-2xl font-semibold mb-4">Backend Health</h2>
                        <button onClick={checkHealth} className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                            Check Health
                        </button>
                        {health && (
                            <div className={`mt-4 p-2 rounded ${health.database === 'connected' ? 'bg-green-200' : 'bg-red-200'}`}>
                                <p>Status: {health.status}</p>
                                <p>Database: {health.database}</p>
                            </div>
                        )}
                    </section>

                    {/* Literature Search */}
                    <section className="mb-8 p-4 bg-white rounded shadow">
                        <h2 className="text-2xl font-semibold mb-4">Literature Search</h2>
                        <form onSubmit={handleSearch}>
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search for articles..."
                                className="w-full p-2 border rounded"
                            />
                            <button type="submit" className="mt-2 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                                Search
                            </button>
                        </form>
                        <div className="mt-4">
                            {searchResults.map((result, index) => (
                                <div key={index} className="p-4 bg-gray-200 rounded mb-2">
                                    <h3 className="font-bold">{result.title}</h3>
                                    <p>{result.abstract}</p>
                                </div>
                            ))}
                        </div>
                    </section>

                    {/* Hypothesis Generator */}
                    <section className="p-4 bg-white rounded shadow">
                        <h2 className="text-2xl font-semibold mb-4">Hypothesis Generator</h2>
                        <form onSubmit={generateHypothesis}>
                            <textarea
                                value={hypothesisInput}
                                onChange={(e) => setHypothesisInput(e.target.value)}
                                placeholder="Enter a disease, protein, or compound..."
                                className="w-full p-2 border rounded"
                                rows="3"
                            ></textarea>
                            <button type="submit" className="mt-2 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                                Generate Hypothesis
                            </button>
                        </form>
                        {hypothesis && (
                            <div className="mt-4 p-4 bg-green-100 rounded">
                                <p className="font-semibold">Suggested Hypothesis:</p>
                                <p>{hypothesis}</p>
                            </div>
                        )}
                    </section>
                </div>
            </main>
        </div>
    );
}

export default App;