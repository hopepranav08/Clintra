import React from 'react';

const ClintraLogo = ({ size = 'md', onClick, className = '' }) => {
    const sizes = {
        sm: { width: '32px', height: '32px' },
        md: { width: '48px', height: '48px' },
        lg: { width: '64px', height: '64px' },
        xl: { width: '80px', height: '80px' }
    };

    return (
        <div 
            onClick={onClick}
            className={`${onClick ? 'cursor-pointer hover:scale-110 transition-transform duration-300' : ''} ${className} flex-shrink-0`}
            style={sizes[size]}
        >
            <svg 
                width="100%" 
                height="100%" 
                viewBox="0 0 200 200" 
                xmlns="http://www.w3.org/2000/svg"
                className="w-full h-full"
            >
                <defs>
                    {/* Primary gradient for DNA helix - Literature theme */}
                    <linearGradient id="dnaGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#00E6FF" /> {/* Clintra Teal - Literature */}
                        <stop offset="50%" stopColor="#00FFFF" /> {/* Clintra Cyan - Literature */}
                        <stop offset="100%" stopColor="#0891B2" /> {/* Darker Teal - Literature */}
                    </linearGradient>
                    
                    {/* Secondary gradient for molecular bonds - Hypothesis/Download theme */}
                    <linearGradient id="bondGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#7C3AED" /> {/* Clintra Purple - Hypothesis */}
                        <stop offset="50%" stopColor="#FBBF24" /> {/* Clintra Gold - Download */}
                        <stop offset="100%" stopColor="#EC4899" /> {/* Clintra Pink - Download */}
                    </linearGradient>
                    
                    {/* AI/Data gradient - All sections combined */}
                    <linearGradient id="aiGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#7C3AED" /> {/* Purple - Hypothesis */}
                        <stop offset="25%" stopColor="#00E6FF" /> {/* Teal - Literature */}
                        <stop offset="50%" stopColor="#FBBF24" /> {/* Gold - Download */}
                        <stop offset="75%" stopColor="#EC4899" /> {/* Pink - Download */}
                        <stop offset="100%" stopColor="#10B981" /> {/* Emerald - AI */}
                    </linearGradient>
                    
                    {/* Literature section gradient */}
                    <linearGradient id="literatureGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#00E6FF" /> {/* Clintra Teal */}
                        <stop offset="100%" stopColor="#0891B2" /> {/* Darker Teal */}
                    </linearGradient>
                    
                    {/* Hypothesis section gradient */}
                    <linearGradient id="hypothesisGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#7C3AED" /> {/* Clintra Purple */}
                        <stop offset="100%" stopColor="#A855F7" /> {/* Purple Bright */}
                    </linearGradient>
                    
                    {/* Download section gradient */}
                    <linearGradient id="downloadGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#FBBF24" /> {/* Clintra Gold */}
                        <stop offset="100%" stopColor="#FCD34D" /> {/* Gold Bright */}
                    </linearGradient>
                    
                    {/* Glow effect */}
                    <filter id="glow">
                        <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                        <feMerge> 
                            <feMergeNode in="coloredBlur"/>
                            <feMergeNode in="SourceGraphic"/>
                        </feMerge>
                    </filter>
                    
                    {/* Shadow effect */}
                    <filter id="shadow">
                        <feDropShadow dx="1" dy="1" stdDeviation="1" floodColor="rgba(0,0,0,0.4)"/>
                    </filter>
                    
                    {/* Strong glow for highlights */}
                    <filter id="strongGlow">
                        <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                        <feMerge> 
                            <feMergeNode in="coloredBlur"/>
                            <feMergeNode in="SourceGraphic"/>
                        </feMerge>
                    </filter>
                </defs>

                {/* Background subtle pattern */}
                <rect width="200" height="200" fill="rgba(0,0,0,0.02)" />

                {/* Central DNA Double Helix */}
                <g transform="translate(100,100)" filter="url(#shadow)">
                    {/* DNA Helix Structure - Left strand */}
                    <path 
                        d="M -35 -70 Q -45 -50 -35 -30 Q -25 -10 -35 10 Q -45 30 -35 50 Q -25 70 -35 70" 
                        fill="none" 
                        stroke="url(#dnaGradient)" 
                        strokeWidth="5" 
                        filter="url(#strongGlow)"
                        opacity="0.95"
                    />
                    
                    {/* DNA Helix Structure - Right strand */}
                    <path 
                        d="M 35 -70 Q 45 -50 35 -30 Q 25 -10 35 10 Q 45 30 35 50 Q 25 70 35 70" 
                        fill="none" 
                        stroke="url(#dnaGradient)" 
                        strokeWidth="5" 
                        filter="url(#strongGlow)"
                        opacity="0.95"
                    />
                    
                    {/* DNA Base Pairs (connecting lines) */}
                    <line x1="-35" y1="-70" x2="35" y2="-70" stroke="url(#bondGradient)" strokeWidth="3" opacity="0.9" filter="url(#glow)"/>
                    <line x1="-35" y1="-30" x2="35" y2="-30" stroke="url(#bondGradient)" strokeWidth="3" opacity="0.9" filter="url(#glow)"/>
                    <line x1="-35" y1="10" x2="35" y2="10" stroke="url(#bondGradient)" strokeWidth="3" opacity="0.9" filter="url(#glow)"/>
                    <line x1="-35" y1="50" x2="35" y2="50" stroke="url(#bondGradient)" strokeWidth="3" opacity="0.9" filter="url(#glow)"/>
                    <line x1="-35" y1="70" x2="35" y2="70" stroke="url(#bondGradient)" strokeWidth="3" opacity="0.9" filter="url(#glow)"/>
                    
                    {/* Central research core */}
                    <circle cx="0" cy="0" r="12" fill="url(#dnaGradient)" filter="url(#strongGlow)"/>
                    
                    {/* Molecular bonds extending from center */}
                    <line x1="0" y1="0" x2="-28" y2="-18" stroke="url(#bondGradient)" strokeWidth="4" opacity="0.8" filter="url(#glow)"/>
                    <line x1="0" y1="0" x2="28" y2="-18" stroke="url(#bondGradient)" strokeWidth="4" opacity="0.8" filter="url(#glow)"/>
                    <line x1="0" y1="0" x2="-28" y2="18" stroke="url(#bondGradient)" strokeWidth="4" opacity="0.8" filter="url(#glow)"/>
                    <line x1="0" y1="0" x2="28" y2="18" stroke="url(#bondGradient)" strokeWidth="4" opacity="0.8" filter="url(#glow)"/>
                    
                    {/* Terminal research atoms - Section themed colors */}
                    <circle cx="-28" cy="-18" r="6" fill="url(#literatureGradient)" filter="url(#strongGlow)"/>
                    <circle cx="28" cy="-18" r="6" fill="url(#hypothesisGradient)" filter="url(#strongGlow)"/>
                    <circle cx="-28" cy="18" r="6" fill="url(#downloadGradient)" filter="url(#strongGlow)"/>
                    <circle cx="28" cy="18" r="6" fill="url(#aiGradient)" filter="url(#strongGlow)"/>
                </g>
                
                {/* AI/Research Network Elements */}
                <g transform="translate(100,100)" opacity="0.7">
                    {/* Neural network nodes */}
                    <circle cx="-75" cy="-75" r="4" fill="url(#aiGradient)" filter="url(#glow)"/>
                    <circle cx="75" cy="-75" r="4" fill="url(#aiGradient)" filter="url(#glow)"/>
                    <circle cx="-75" cy="75" r="4" fill="url(#aiGradient)" filter="url(#glow)"/>
                    <circle cx="75" cy="75" r="4" fill="url(#aiGradient)" filter="url(#glow)"/>
                    
                    {/* AI connections */}
                    <line x1="-75" y1="-75" x2="75" y2="75" stroke="url(#aiGradient)" strokeWidth="1.5" opacity="0.4"/>
                    <line x1="75" y1="-75" x2="-75" y2="75" stroke="url(#aiGradient)" strokeWidth="1.5" opacity="0.4"/>
                    <line x1="-75" y1="-75" x2="75" y2="-75" stroke="url(#aiGradient)" strokeWidth="1.5" opacity="0.4"/>
                    <line x1="-75" y1="75" x2="75" y2="75" stroke="url(#aiGradient)" strokeWidth="1.5" opacity="0.4"/>
                </g>
                
                {/* Research Data Flow Indicators - Section Themed */}
                <g transform="translate(100,100)" opacity="0.5">
                    {/* Data particles flowing - Section colors */}
                    <circle cx="0" cy="-85" r="3" fill="url(#literatureGradient)" filter="url(#glow)"/>
                    <circle cx="0" cy="85" r="3" fill="url(#hypothesisGradient)" filter="url(#glow)"/>
                    <circle cx="-85" cy="0" r="3" fill="url(#downloadGradient)" filter="url(#glow)"/>
                    <circle cx="85" cy="0" r="3" fill="url(#aiGradient)" filter="url(#glow)"/>
                    
                    {/* Data flow lines - Section themed */}
                    <path d="M 0 -85 Q -20 -70 -40 -55" fill="none" stroke="url(#literatureGradient)" strokeWidth="2" opacity="0.6"/>
                    <path d="M 0 85 Q 20 70 40 55" fill="none" stroke="url(#hypothesisGradient)" strokeWidth="2" opacity="0.6"/>
                    <path d="M -85 0 Q -70 -20 -55 -40" fill="none" stroke="url(#downloadGradient)" strokeWidth="2" opacity="0.6"/>
                    <path d="M 85 0 Q 70 20 55 40" fill="none" stroke="url(#aiGradient)" strokeWidth="2" opacity="0.6"/>
                </g>
                
                {/* Pulsing research activity */}
                <g transform="translate(100,100)">
                    <circle cx="0" cy="0" r="90" fill="none" stroke="url(#dnaGradient)" strokeWidth="1" opacity="0.3">
                        <animate attributeName="r" values="90;95;90" dur="4s" repeatCount="indefinite"/>
                        <animate attributeName="opacity" values="0.3;0.6;0.3" dur="4s" repeatCount="indefinite"/>
                    </circle>
                </g>
            </svg>
        </div>
    );
};

export default ClintraLogo;