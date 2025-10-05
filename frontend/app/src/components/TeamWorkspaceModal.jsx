import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const TeamWorkspaceModal = ({ isOpen, onClose, user }) => {
    const [workspaces, setWorkspaces] = useState([]);
    const [currentWorkspace, setCurrentWorkspace] = useState(null);
    const [newWorkspaceName, setNewWorkspaceName] = useState('');
    const [newWorkspaceDescription, setNewWorkspaceDescription] = useState('');
    const [inviteEmail, setInviteEmail] = useState('');
    const [inviteRole, setInviteRole] = useState('member');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);

    // Load workspaces when modal opens
    React.useEffect(() => {
        if (isOpen && user) {
            loadWorkspaces();
        }
    }, [isOpen, user]);

    const loadWorkspaces = async () => {
        try {
            const token = localStorage.getItem('token');
            if (token && user) {
                const response = await axios.get(`${API_URL}/api/workspaces`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setWorkspaces(response.data);
                
                // Auto-select first workspace if none selected
                if (!currentWorkspace && response.data.length > 0) {
                    setCurrentWorkspace(response.data[0]);
                }
            }
        } catch (error) {
            console.error('Error loading workspaces:', error);
            setError('Failed to load workspaces');
        }
    };

    const createWorkspace = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');

        try {
            const token = localStorage.getItem('token');
            if (token && user) {
                const response = await axios.post(`${API_URL}/api/workspaces`, {
                    name: newWorkspaceName,
                    description: newWorkspaceDescription
                }, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                
                const newWorkspace = response.data;
                setWorkspaces(prev => [...prev, newWorkspace]);
                setCurrentWorkspace(newWorkspace);
                setNewWorkspaceName('');
                setNewWorkspaceDescription('');
                setSuccess('Workspace created successfully!');
                
                console.log('✅ Workspace created:', newWorkspace);
            }
        } catch (error) {
            console.error('Error creating workspace:', error);
            setError('Failed to create workspace. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const inviteToWorkspace = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');

        try {
            const token = localStorage.getItem('token');
            if (token && user && currentWorkspace) {
                const response = await axios.post(`${API_URL}/api/workspaces/${currentWorkspace.id}/invite`, {
                    user_email: inviteEmail,
                    role: inviteRole
                }, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                
                setInviteEmail('');
                setInviteRole('member');
                setSuccess('Team member invited successfully!');
                
                console.log('✅ Team member invited:', response.data);
            } else {
                setError('Please select a workspace first');
            }
        } catch (error) {
            console.error('Error inviting team member:', error);
            setError('Failed to invite team member. Please check the email and try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        setError('');
        setSuccess('');
        setNewWorkspaceName('');
        setNewWorkspaceDescription('');
        setInviteEmail('');
        setInviteRole('member');
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div 
            className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={(e) => {
                if (e.target === e.currentTarget) {
                    handleClose();
                }
            }}
        >
            <div className="bg-clintra-navy-light border border-clintra-teal/30 rounded-xl p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-2xl font-bold text-clintra-cyan flex items-center space-x-2">
                        <span>👥</span>
                        <span>Team Workspace</span>
                    </h3>
                    <button
                        onClick={handleClose}
                        className="text-clintra-teal/60 hover:text-clintra-cyan transition-colors"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                
                <div className="grid md:grid-cols-2 gap-6">
                    {/* Create New Workspace */}
                    <div className="bg-clintra-navy/50 border border-clintra-teal/20 rounded-lg p-4">
                        <h4 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                            <span>🏢</span>
                            <span>Create Workspace</span>
                        </h4>
                        <form onSubmit={createWorkspace}>
                            <input
                                type="text"
                                value={newWorkspaceName}
                                onChange={(e) => setNewWorkspaceName(e.target.value)}
                                placeholder="Workspace name"
                                className="w-full px-3 py-2 bg-clintra-navy border border-clintra-teal/30 rounded-lg text-white placeholder-clintra-teal/60 focus:border-clintra-teal focus:outline-none mb-3"
                                required
                            />
                            <textarea
                                value={newWorkspaceDescription}
                                onChange={(e) => setNewWorkspaceDescription(e.target.value)}
                                placeholder="Workspace description (optional)"
                                rows={3}
                                className="w-full px-3 py-2 bg-clintra-navy border border-clintra-teal/30 rounded-lg text-white placeholder-clintra-teal/60 focus:border-clintra-teal focus:outline-none mb-4"
                            />
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full bg-gradient-to-r from-clintra-teal to-clintra-cyan text-white py-2 px-4 rounded-lg hover:from-clintra-teal/80 hover:to-clintra-cyan/80 transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? 'Creating...' : 'Create Workspace'}
                            </button>
                        </form>
                    </div>
                    
                    {/* Invite Team Members */}
                    <div className="bg-clintra-navy/50 border border-clintra-teal/20 rounded-lg p-4">
                        <h4 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                            <span>👥</span>
                            <span>Invite Members</span>
                        </h4>
                        <form onSubmit={inviteToWorkspace}>
                            <input
                                type="email"
                                value={inviteEmail}
                                onChange={(e) => setInviteEmail(e.target.value)}
                                placeholder="Member email"
                                className="w-full px-3 py-2 bg-clintra-navy border border-clintra-teal/30 rounded-lg text-white placeholder-clintra-teal/60 focus:border-clintra-teal focus:outline-none mb-3"
                                required
                            />
                            <select
                                value={inviteRole}
                                onChange={(e) => setInviteRole(e.target.value)}
                                className="w-full px-3 py-2 bg-clintra-navy border border-clintra-teal/30 rounded-lg text-white focus:border-clintra-teal focus:outline-none mb-4"
                            >
                                <option value="member">Member</option>
                                <option value="admin">Admin</option>
                            </select>
                            <button
                                type="submit"
                                disabled={loading || !currentWorkspace}
                                className="w-full bg-gradient-to-r from-clintra-purple to-clintra-pink text-white py-2 px-4 rounded-lg hover:from-clintra-purple/80 hover:to-clintra-pink/80 transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? 'Inviting...' : 'Send Invitation'}
                            </button>
                        </form>
                    </div>
                </div>
                
                {/* Current Workspaces */}
                {workspaces.length > 0 && (
                    <div className="mt-6">
                        <h4 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                            <span>🏢</span>
                            <span>Your Workspaces</span>
                        </h4>
                        <div className="space-y-3">
                            {workspaces.map((workspace) => (
                                <div key={workspace.id} className="bg-clintra-navy/30 border border-clintra-teal/20 rounded-lg p-3 flex items-center justify-between">
                                    <div>
                                        <h5 className="text-white font-medium">{workspace.name}</h5>
                                        <p className="text-clintra-teal/60 text-sm">{workspace.description}</p>
                                    </div>
                                    <button
                                        onClick={() => setCurrentWorkspace(workspace)}
                                        className={`px-3 py-1 rounded-lg text-sm font-medium transition-all duration-200 ${
                                            currentWorkspace?.id === workspace.id
                                                ? 'bg-clintra-teal text-white'
                                                : 'bg-clintra-teal/20 text-clintra-teal hover:bg-clintra-teal hover:text-white'
                                        }`}
                                    >
                                        {currentWorkspace?.id === workspace.id ? 'Active' : 'Select'}
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
                
                {/* Status Messages */}
                {error && (
                    <div className="mt-4 bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                        <p className="text-red-400 text-sm">{error}</p>
                    </div>
                )}
                
                {success && (
                    <div className="mt-4 bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                        <p className="text-green-400 text-sm">{success}</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default TeamWorkspaceModal;
