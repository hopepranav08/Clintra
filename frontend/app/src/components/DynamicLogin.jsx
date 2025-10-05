import React, { useState } from 'react';
import ClintraLogo from './ClintraLogo';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const DynamicLogin = ({ onLogin }) => {
    const [isSignup, setIsSignup] = useState(false);
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        
        // Validation for both login and signup
        if (!formData.email || !formData.email.includes('@')) {
            setError('Please enter a valid email address');
            setLoading(false);
            return;
        }

        if (!formData.password || formData.password.length < 6) {
            setError('Password must be at least 6 characters');
            setLoading(false);
            return;
        }
        
        // Additional validation for signup
        if (isSignup) {
            if (!formData.username || formData.username.trim().length < 3) {
                setError('Username must be at least 3 characters');
                setLoading(false);
                return;
            }
            
            if (formData.password !== formData.confirmPassword) {
                setError('Passwords do not match');
                setLoading(false);
                return;
            }
        }
        
        try {
            if (isSignup) {
                // Register new user
                const response = await axios.post(`${API_URL}/api/auth/register`, {
                    username: formData.username,
                    email: formData.email,
                    password: formData.password,
                    full_name: formData.username.charAt(0).toUpperCase() + formData.username.slice(1)
                });
                
                // Auto-login after successful registration
                const loginResponse = await axios.post(`${API_URL}/api/auth/login`, {
                    username: formData.username,
                    password: formData.password
                });
                
                const { access_token, user } = loginResponse.data;
                localStorage.setItem('token', access_token);
                localStorage.setItem('user', JSON.stringify(user));
                setLoading(false);
                onLogin(user, access_token);
                
            } else {
                // Login existing user - backend now handles email/username lookup
                const loginResponse = await axios.post(`${API_URL}/api/auth/login`, {
                    username: formData.email, // Backend will try email, username, or username from email
                    password: formData.password
                });
                
                const { access_token, user } = loginResponse.data;
                localStorage.setItem('token', access_token);
                localStorage.setItem('user', JSON.stringify(user));
                setLoading(false);
                onLogin(user, access_token);
            }
        } catch (error) {
            setLoading(false);
            console.error('Authentication error:', error);
            
            if (error.response?.data?.detail) {
                setError(error.response.data.detail);
            } else if (error.response?.data?.message) {
                setError(error.response.data.message);
            } else if (error.response?.status === 401) {
                setError('Invalid credentials. Please check your email/username and password.');
            } else if (error.response?.status === 400) {
                setError('Invalid request. Please check your input.');
            } else if (error.response?.status === 409) {
                setError('User already exists. Please try logging in instead.');
            } else if (error.code === 'NETWORK_ERROR' || !error.response) {
                setError('Unable to connect to server. Please check your connection.');
            } else {
                setError(isSignup ? 'Registration failed. Please try again.' : 'Login failed. Please check your credentials.');
            }
        }
    };

    const handleInputChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
        setError(''); // Clear error on input change
    };

    const switchMode = (mode) => {
        setIsSignup(mode);
        setError('');
        // Keep email and password, clear username and confirm password
        setFormData(prev => ({
            ...prev,
            confirmPassword: ''
        }));
    };

    return (
        <div className="min-h-screen bg-clintra-navy-darker relative overflow-hidden">
            {/* Full Screen Dark Background */}
            <div className="absolute inset-0 bg-gradient-to-br from-clintra-navy-darker via-clintra-navy-dark to-clintra-navy"></div>
            
            {/* Subtle Animated Background */}
            <div className="absolute inset-0 opacity-10">
                <div className="absolute top-1/4 left-1/4 w-64 h-64 rounded-full bg-clintra-teal/20 animate-pulse" style={{animationDelay: '0s', animationDuration: '6s'}}></div>
                <div className="absolute bottom-1/4 right-1/4 w-48 h-48 rounded-full bg-clintra-cyan/20 animate-pulse" style={{animationDelay: '3s', animationDuration: '8s'}}></div>
                <div className="absolute top-3/4 left-1/2 w-32 h-32 rounded-full bg-white/10 animate-pulse" style={{animationDelay: '1.5s', animationDuration: '5s'}}></div>
            </div>

            {/* Full Screen Layout */}
            <div className="relative z-10 min-h-screen flex">
                {/* Left Side - Branding (45%) */}
                <div className="w-[45%] flex flex-col justify-center items-center px-12 py-16">
                    <div className="max-w-md text-center">
                        {/* Logo */}
                        <div className="mb-8">
                            <ClintraLogo size="xl" className="mx-auto hover:scale-110 transition-transform duration-500" />
                        </div>
                        
                        {/* Brand Name */}
                        <h1 className="text-4xl font-black text-white mb-6 tracking-tight">
                            CLINTRA
                        </h1>
                        
                        {/* Welcome Message */}
                        <p className="text-white/90 text-lg leading-relaxed mb-8">
                            {isSignup 
                                ? 'Join the future of AI-powered biomedical research'
                                : 'Welcome back! Continue your research journey'
                            }
                        </p>
                        
                        {/* Feature highlights */}
                        <div className="space-y-4">
                            <div className="flex items-center justify-center space-x-3 text-white/90">
                                <div className="w-2 h-2 bg-clintra-cyan rounded-full animate-pulse" style={{animationDelay: '0s'}}></div>
                                <span className="text-base font-semibold">Smart Literature Analysis</span>
                            </div>
                            <div className="flex items-center justify-center space-x-3 text-white/90">
                                <div className="w-2 h-2 bg-clintra-teal rounded-full animate-pulse" style={{animationDelay: '0.5s'}}></div>
                                <span className="text-base font-semibold">3D Molecular Visualization</span>
                            </div>
                            <div className="flex items-center justify-center space-x-3 text-white/90">
                                <div className="w-2 h-2 bg-white/90 rounded-full animate-pulse" style={{animationDelay: '1s'}}></div>
                                <span className="text-base font-semibold">AI-Powered Research Insights</span>
                            </div>
                        </div>

                        {/* Additional Visual Elements */}
                        <div className="mt-12 space-y-6">
                            {/* Stats or Trust Elements */}
                            <div className="flex items-center justify-center space-x-8 text-white/60 text-sm">
                                <div className="text-center">
                                    <div className="text-lg font-bold text-clintra-cyan">10K+</div>
                                    <div className="text-xs">Research Papers</div>
                                </div>
                                <div className="w-px h-8 bg-white/20"></div>
                                <div className="text-center">
                                    <div className="text-lg font-bold text-clintra-teal">500+</div>
                                    <div className="text-xs">Active Users</div>
                                </div>
                                <div className="w-px h-8 bg-white/20"></div>
                                <div className="text-center">
                                    <div className="text-lg font-bold text-white">99.9%</div>
                                    <div className="text-xs">Uptime</div>
                                </div>
                            </div>
                            
                            {/* Subtle decorative elements */}
                            <div className="flex items-center justify-center space-x-4 opacity-30">
                                <div className="w-8 h-px bg-clintra-cyan"></div>
                                <div className="w-1 h-1 bg-clintra-cyan rounded-full"></div>
                                <div className="w-12 h-px bg-clintra-teal"></div>
                                <div className="w-1 h-1 bg-clintra-teal rounded-full"></div>
                                <div className="w-8 h-px bg-clintra-cyan"></div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Side - Form (55%) */}
                <div className="w-[55%] flex flex-col justify-center items-center px-8 py-16 relative">
                    {/* Toggle Button - Top Right */}
                    <div className="absolute top-8 right-8">
                        <div className="bg-clintra-navy-dark/80 backdrop-blur-sm border border-clintra-teal/30 rounded-2xl p-1 shadow-xl">
                            <div className="relative flex">
                                <button
                                    onClick={() => switchMode(false)}
                                    className={`px-6 py-3 rounded-xl text-sm font-bold transition-all duration-500 ease-in-out relative z-10 ${
                                        !isSignup 
                                            ? 'bg-clintra-teal text-white shadow-lg transform scale-105' 
                                            : 'text-clintra-cyan hover:text-clintra-cyan-bright'
                                    }`}
                                >
                                    Login
                                </button>
                                <button
                                    onClick={() => switchMode(true)}
                                    className={`px-6 py-3 rounded-xl text-sm font-bold transition-all duration-500 ease-in-out relative z-10 ${
                                        isSignup 
                                            ? 'bg-clintra-teal text-white shadow-lg transform scale-105' 
                                            : 'text-clintra-cyan hover:text-clintra-cyan-bright'
                                    }`}
                                >
                                    Sign Up
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Form Container */}
                    <div className="w-full max-w-md">
                        {/* Form Header */}
                        <div className="text-center mb-6">
                            <h2 className="text-3xl font-bold mb-2 text-white">
                                {isSignup ? 'Create Account' : 'Welcome Back'}
                            </h2>
                            <p className="text-white/70 text-base">
                                {isSignup ? 'Join the research revolution' : 'Sign in to continue your journey'}
                            </p>
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div className="mb-5 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm backdrop-blur-sm">
                                <div className="flex items-center space-x-2">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    <span className="font-medium">{error}</span>
                                </div>
                            </div>
                        )}

                        {/* Form */}
                        <form onSubmit={handleSubmit} className="space-y-4">
                            {isSignup && (
                                <div className="animate-fade-in">
                                    <label className="block text-white/90 text-sm font-semibold mb-2">Username</label>
                                    <input
                                        type="text"
                                        name="username"
                                        value={formData.username}
                                        onChange={handleInputChange}
                                        className="w-full px-4 py-3 bg-clintra-navy-dark/80 border border-clintra-teal/30 rounded-xl text-white placeholder-white/50 focus:outline-none focus:border-clintra-teal focus:ring-2 focus:ring-clintra-teal/20 transition-all text-sm backdrop-blur-sm"
                                        placeholder="Choose a unique username"
                                        required
                                    />
                                </div>
                            )}

                            <div className="animate-fade-in">
                                <label className="block text-white/90 text-sm font-semibold mb-2">Email</label>
                                <input
                                    type="email"
                                    name="email"
                                    value={formData.email}
                                    onChange={handleInputChange}
                                    className="w-full px-4 py-3 bg-clintra-navy-dark/80 border border-clintra-teal/30 rounded-xl text-white placeholder-white/50 focus:outline-none focus:border-clintra-teal focus:ring-2 focus:ring-clintra-teal/20 transition-all text-sm backdrop-blur-sm"
                                    placeholder="Enter your email address"
                                    required
                                />
                            </div>

                            <div className="animate-fade-in">
                                <label className="block text-white/90 text-sm font-semibold mb-2">Password</label>
                                <div className="relative">
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        name="password"
                                        value={formData.password}
                                        onChange={handleInputChange}
                                        className="w-full px-4 py-3 pr-12 bg-clintra-navy-dark/80 border border-clintra-teal/30 rounded-xl text-white placeholder-white/50 focus:outline-none focus:border-clintra-teal focus:ring-2 focus:ring-clintra-teal/20 transition-all text-sm backdrop-blur-sm"
                                        placeholder={isSignup ? "Create a secure password" : "Enter your password"}
                                        required
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute inset-y-0 right-0 pr-3 flex items-center hover:bg-clintra-teal/10 rounded-r-xl transition-colors"
                                    >
                                        {showPassword ? (
                                            <svg className="h-4 w-4 text-white/50 hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                                            </svg>
                                        ) : (
                                            <svg className="h-4 w-4 text-white/50 hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                            </svg>
                                        )}
                                    </button>
                                </div>
                            </div>

                            {isSignup && (
                                <div className="animate-fade-in">
                                    <label className="block text-white/90 text-sm font-semibold mb-2">Confirm Password</label>
                                    <div className="relative">
                                        <input
                                            type={showConfirmPassword ? "text" : "password"}
                                            name="confirmPassword"
                                            value={formData.confirmPassword}
                                            onChange={handleInputChange}
                                            className="w-full px-4 py-3 pr-12 bg-clintra-navy-dark/80 border border-clintra-teal/30 rounded-xl text-white placeholder-white/50 focus:outline-none focus:border-clintra-teal focus:ring-2 focus:ring-clintra-teal/20 transition-all text-sm backdrop-blur-sm"
                                            placeholder="Confirm your password"
                                            required
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                            className="absolute inset-y-0 right-0 pr-3 flex items-center hover:bg-clintra-teal/10 rounded-r-xl transition-colors"
                                        >
                                            {showConfirmPassword ? (
                                                <svg className="h-4 w-4 text-white/50 hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                                                </svg>
                                            ) : (
                                                <svg className="h-4 w-4 text-white/50 hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                                </svg>
                                            )}
                                        </button>
                                    </div>
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-4 px-6 bg-gradient-to-r from-clintra-teal to-clintra-cyan hover:from-clintra-cyan hover:to-clintra-teal text-white rounded-xl font-bold text-base transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 hover:shadow-xl group"
                            >
                                {loading ? (
                                    <span className="flex items-center justify-center">
                                        <div className="flex space-x-1">
                                            <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                                            <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                                            <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                                        </div>
                                        <span className="ml-3 text-base">Processing...</span>
                                    </span>
                                ) : (
                                    <span className="flex items-center justify-center">
                                        <span>{isSignup ? 'Create Account' : 'Sign In'}</span>
                                        <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                        </svg>
                                    </span>
                                )}
                            </button>
                        </form>

                        {/* Additional Elements for Visual Interest */}
                        <div className="mt-6 space-y-4">
                            {/* Trust Indicators */}
                            <div className="flex items-center justify-center space-x-6 text-white/50 text-xs">
                                <div className="flex items-center space-x-1">
                                    <div className="w-2 h-2 bg-clintra-cyan rounded-full animate-pulse"></div>
                                    <span>Secure</span>
                                </div>
                                <div className="flex items-center space-x-1">
                                    <div className="w-2 h-2 bg-clintra-teal rounded-full animate-pulse" style={{animationDelay: '0.5s'}}></div>
                                    <span>AI-Powered</span>
                                </div>
                                <div className="flex items-center space-x-1">
                                    <div className="w-2 h-2 bg-clintra-cyan rounded-full animate-pulse" style={{animationDelay: '1s'}}></div>
                                    <span>Research</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DynamicLogin;
