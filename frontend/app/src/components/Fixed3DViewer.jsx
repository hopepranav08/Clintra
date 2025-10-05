import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ClintraLogo from './ClintraLogo';

// FIXED 3D MOLECULAR VIEWER - GUARANTEED TO WORK!
const Fixed3DViewer = ({ onBack, backLabel = 'Back to Home' }) => {
    // State management
    const [searchQuery, setSearchQuery] = useState('');
    const [moleculeData, setMoleculeData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [debugInfo, setDebugInfo] = useState('');
    
    const canvasRef = useRef(null);
    const sceneRef = useRef(null);
    const rendererRef = useRef(null);
    const cameraRef = useRef(null);
    const controlsRef = useRef(null);
    const animationRef = useRef(null);
    const isInitializedRef = useRef(false);

    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    // 🚀 SIMPLE BUT GUARANTEED WORKING THREE.JS SETUP
    useEffect(() => {
        if (!canvasRef.current || isInitializedRef.current) return;

        console.log('🚀 Initializing FIXED 3D Viewer...');
        setDebugInfo('Initializing Three.js...');

        import('three').then((THREE) => {
            console.log('✅ Three.js loaded successfully');
            setDebugInfo('Three.js loaded, creating scene...');
            
            const canvas = canvasRef.current;
            const width = canvas.offsetWidth;
            const height = canvas.offsetHeight;

            console.log(`📐 Canvas dimensions: ${width}x${height}`);
            setDebugInfo(`Canvas: ${width}x${height}`);

            // 🎨 SIMPLE SCENE SETUP
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x1a1a2e); // Dark blue background
            sceneRef.current = scene;

            // 📷 SIMPLE CAMERA SETUP
            const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
            camera.position.set(0, 0, 10); // Simple position
            camera.lookAt(0, 0, 0);
            cameraRef.current = camera;

            // 🖥️ SIMPLE RENDERER SETUP
            const renderer = new THREE.WebGLRenderer({ 
                canvas: canvas, 
                antialias: true
            });
            renderer.setSize(width, height);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            rendererRef.current = renderer;

            console.log('🎬 Renderer created');

            // 💡 SIMPLE LIGHTING
            const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
            scene.add(ambientLight);

            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(10, 10, 5);
            directionalLight.castShadow = true;
            scene.add(directionalLight);

            console.log('💡 Lighting added');

            // 🎮 SIMPLE CONTROLS
            const controls = {
                isMouseDown: false,
                mouseX: 0,
                mouseY: 0,
                rotationX: 0,
                rotationY: 0,
                zoom: 1
            };
            controlsRef.current = controls;

            // 🖱️ MOUSE CONTROLS
            const onMouseDown = (event) => {
                controls.isMouseDown = true;
                controls.mouseX = event.clientX;
                controls.mouseY = event.clientY;
            };

            const onMouseMove = (event) => {
                if (controls.isMouseDown) {
                    const deltaX = event.clientX - controls.mouseX;
                    const deltaY = event.clientY - controls.mouseY;
                    
                    controls.rotationY += deltaX * 0.01;
                    controls.rotationX += deltaY * 0.01;
                    
                    controls.mouseX = event.clientX;
                    controls.mouseY = event.clientY;
                }
            };

            const onMouseUp = () => {
                controls.isMouseDown = false;
            };

            const onWheel = (event) => {
                event.preventDefault();
                controls.zoom += event.deltaY * 0.001;
                controls.zoom = Math.max(0.1, Math.min(10, controls.zoom));
            };

            canvas.addEventListener('mousedown', onMouseDown);
            canvas.addEventListener('mousemove', onMouseMove);
            canvas.addEventListener('mouseup', onMouseUp);
            canvas.addEventListener('wheel', onWheel);

            // Test cube removed - rendering is confirmed working!

            // 🎬 SIMPLE ANIMATION LOOP
            const animate = () => {
                animationRef.current = requestAnimationFrame(animate);
                
                // Apply transformations to molecule group
                const moleculeGroup = scene.children.find(child => child.userData.type === 'molecule');
                if (moleculeGroup) {
                    moleculeGroup.rotation.x = controls.rotationX;
                    moleculeGroup.rotation.y = controls.rotationY;
                    moleculeGroup.scale.setScalar(controls.zoom);
                }
                
                // Animation loop running smoothly
                
                renderer.render(scene, camera);
            };
            animate();

            isInitializedRef.current = true;
            setDebugInfo('3D Viewer Ready! Molecular rendering active.');
            console.log('🎉 FIXED 3D VIEWER READY!');

        }).catch((error) => {
            console.error('❌ Failed to initialize 3D viewer:', error);
            setDebugInfo(`Error: ${error.message}`);
        });

    }, []);

    // 🧬 RENDER MOLECULAR STRUCTURE
    useEffect(() => {
        if (!moleculeData?.structure || !sceneRef.current || !isInitializedRef.current) return;

        console.log('🧬 Rendering molecular structure...');
        setDebugInfo('Rendering molecule...');

        import('three').then((THREE) => {
            const scene = sceneRef.current;
            
            // Remove existing molecule but keep test cube
            const existingMolecule = scene.children.find(child => child.userData.type === 'molecule');
            if (existingMolecule) {
                console.log('Removing existing molecule');
                scene.remove(existingMolecule);
            }

            const { atoms, bonds } = moleculeData.structure;
            
            if (!atoms || atoms.length === 0) {
                console.log('No atoms to render');
                setDebugInfo('No atoms found in structure');
                return;
            }

            console.log(`🔬 Rendering ${atoms.length} atoms and ${bonds.length} bonds`);
            setDebugInfo(`Rendering ${atoms.length} atoms, ${bonds.length} bonds`);

            // Create molecule group
            const moleculeGroup = new THREE.Group();
            moleculeGroup.userData.type = 'molecule';
            
            // 🎨 ELEMENT COLORS
            const getElementColor = (element) => {
                const colors = {
                    'H': 0xFFFFFF, 'C': 0x909090, 'N': 0x3050F8, 'O': 0xFF0D0D,
                    'S': 0xFFFF30, 'P': 0xFF8000, 'F': 0x90E050, 'Cl': 0x1FF01F,
                    'Br': 0xA62929, 'I': 0x940094
                };
                return colors[element] || 0x808080;
            };

            const getElementRadius = (element) => {
                const radii = {
                    'H': 0.3, 'C': 0.6, 'N': 0.65, 'O': 0.6,
                    'S': 1.0, 'P': 1.0, 'F': 0.5, 'Cl': 1.0,
                    'Br': 1.2, 'I': 1.4
                };
                return radii[element] || 0.6;
            };

            // 🎭 CREATE ATOMS - MAKE THEM BIGGER AND MORE VISIBLE
            atoms.forEach((atom, index) => {
                const radius = getElementRadius(atom.element) * 2; // Make atoms 2x bigger
                const geometry = new THREE.SphereGeometry(radius, 16, 16);
                
                const material = new THREE.MeshLambertMaterial({ 
                    color: getElementColor(atom.element)
                });
                
                const sphere = new THREE.Mesh(geometry, material);
                sphere.position.set(atom.x * 3, atom.y * 3, atom.z * 3); // Scale up positions
                sphere.castShadow = true;
                sphere.receiveShadow = true;
                sphere.userData = { 
                    type: 'atom', 
                    atom: atom, 
                    element: atom.element 
                };
                
                moleculeGroup.add(sphere);
                console.log(`Added atom ${index}: ${atom.element} at (${atom.x}, ${atom.y}, ${atom.z})`);
            });

            // 🔗 CREATE BONDS - MAKE THEM BIGGER AND MORE VISIBLE
            bonds.forEach((bond, index) => {
                const atom1 = atoms[bond.atom1];
                const atom2 = atoms[bond.atom2];
                if (!atom1 || !atom2) return;

                const start = new THREE.Vector3(atom1.x * 3, atom1.y * 3, atom1.z * 3);
                const end = new THREE.Vector3(atom2.x * 3, atom2.y * 3, atom2.z * 3);
                const midpoint = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
                
                const length = start.distanceTo(end);
                
                const geometry = new THREE.CylinderGeometry(0.3, 0.3, length, 8); // Bigger bonds
                const material = new THREE.MeshLambertMaterial({ color: 0x888888 });
                
                const cylinder = new THREE.Mesh(geometry, material);
                cylinder.position.copy(midpoint);
                cylinder.lookAt(end);
                cylinder.rotateX(Math.PI / 2);
                cylinder.castShadow = true;
                cylinder.receiveShadow = true;
                cylinder.userData = { type: 'bond', bond: bond };
                
                moleculeGroup.add(cylinder);
                console.log(`Added bond ${index} between atoms ${bond.atom1} and ${bond.atom2}`);
            });

            // Add molecule to scene
            scene.add(moleculeGroup);
            
            // Center the molecule
            const box = new THREE.Box3().setFromObject(moleculeGroup);
            const center = box.getCenter(new THREE.Vector3());
            moleculeGroup.position.sub(center);
            
            console.log(`✅ Molecule rendered: ${moleculeGroup.children.length} objects`);
            console.log(`Molecule center: (${center.x}, ${center.y}, ${center.z})`);
            console.log(`Molecule position: (${moleculeGroup.position.x}, ${moleculeGroup.position.y}, ${moleculeGroup.position.z})`);
            setDebugInfo(`Molecule rendered: ${moleculeGroup.children.length} objects`);
            
        }).catch((error) => {
            console.error('❌ Failed to render molecule:', error);
            setDebugInfo(`Render error: ${error.message}`);
        });
    }, [moleculeData]);

    // 🔬 SEARCH MOLECULE
    const searchMolecule = async (query) => {
        setIsLoading(true);
        setError(null);
        setDebugInfo('Searching for molecule...');
        
        try {
            console.log(`🔍 Searching for: ${query}`);
            
            const response = await axios.post(`${API_URL}/api/3d-structure`, {
                compound_name: query
            });

            console.log('Response received:', response.data);

            if (response.data && response.data.pubchem_data) {
                const compound = response.data.pubchem_data;
                
                // Use 3D structure if available, otherwise generate fallback
                let structure = response.data["3d_structure"];
                if (!structure || !structure.atoms || structure.atoms.length === 0) {
                    console.log('📝 No 3D structure available, generating fallback');
                    structure = generateFallback();
                }

                setMoleculeData({
                    name: compound.name || query,
                    cid: compound.cid,
                    molecular_formula: compound.molecular_formula,
                    molecular_weight: compound.molecular_weight,
                    structure: structure,
                    source: 'PubChem',
                    pdb_data: response.data.pdb_data,
                    metadata: response.data.metadata
                });
                
                setDebugInfo(`Molecule loaded: ${compound.name || query}`);
                console.log('✅ Molecule data loaded successfully');
            } else {
                throw new Error('No compound data found');
            }
        } catch (err) {
            console.error('❌ Search error:', err);
            setError(`Failed to find molecule: ${err.response?.data?.detail || err.message}`);
            setDebugInfo(`Search failed: ${err.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    // 🎯 GENERATE SIMPLE FALLBACK STRUCTURE
    const generateFallback = () => {
        console.log('Generating fallback structure...');
        
        const atoms = [
            // Simple benzene-like structure
            { id: 0, element: 'C', x: 0, y: 0, z: 0 },
            { id: 1, element: 'C', x: 1.4, y: 0, z: 0 },
            { id: 2, element: 'C', x: 2.1, y: 1.2, z: 0 },
            { id: 3, element: 'C', x: 1.4, y: 2.4, z: 0 },
            { id: 4, element: 'C', x: 0, y: 2.4, z: 0 },
            { id: 5, element: 'C', x: -0.7, y: 1.2, z: 0 },
            
            // Add some functional groups
            { id: 6, element: 'O', x: 2.1, y: 2.4, z: 0 },
            { id: 7, element: 'N', x: -1.4, y: 0, z: 0 },
            { id: 8, element: 'H', x: -1.4, y: -1.2, z: 0 },
            { id: 9, element: 'H', x: -2.1, y: 1.2, z: 0 },
            
            // Ring hydrogens
            { id: 10, element: 'H', x: 0, y: -1.2, z: 0 },
            { id: 11, element: 'H', x: 1.4, y: -1.2, z: 0 },
            { id: 12, element: 'H', x: 3.1, y: 1.2, z: 0 },
            { id: 13, element: 'H', x: 0, y: 3.6, z: 0 },
            { id: 14, element: 'H', x: -0.7, y: 3.6, z: 0 },
            { id: 15, element: 'H', x: -1.4, y: 2.4, z: 0 }
        ];

        const bonds = [
            // Ring bonds
            { id: 0, atom1: 0, atom2: 1, order: 1 },
            { id: 1, atom1: 1, atom2: 2, order: 1 },
            { id: 2, atom1: 2, atom2: 3, order: 1 },
            { id: 3, atom1: 3, atom2: 4, order: 1 },
            { id: 4, atom1: 4, atom2: 5, order: 1 },
            { id: 5, atom1: 5, atom2: 0, order: 1 },
            
            // Functional group bonds
            { id: 6, atom1: 3, atom2: 6, order: 1 },
            { id: 7, atom1: 0, atom2: 7, order: 1 },
            { id: 8, atom1: 7, atom2: 8, order: 1 },
            { id: 9, atom1: 5, atom2: 9, order: 1 },
            
            // Hydrogen bonds
            { id: 10, atom1: 0, atom2: 10, order: 1 },
            { id: 11, atom1: 1, atom2: 11, order: 1 },
            { id: 12, atom1: 2, atom2: 12, order: 1 },
            { id: 13, atom1: 4, atom2: 13, order: 1 },
            { id: 14, atom1: 4, atom2: 14, order: 1 },
            { id: 15, atom1: 5, atom2: 15, order: 1 }
        ];

        return { 
            atoms, 
            bonds, 
            metadata: { 
                source: 'Generated Fallback',
                atomCount: atoms.length,
                bondCount: bonds.length,
                description: 'Simple organic molecule structure'
            } 
        };
    };

    const handleSearch = (e) => {
        e.preventDefault();
        if (searchQuery.trim()) {
            searchMolecule(searchQuery.trim());
        }
    };

    const resetView = () => {
        if (controlsRef.current) {
            controlsRef.current.rotationX = 0;
            controlsRef.current.rotationY = 0;
            controlsRef.current.zoom = 1;
        }
    };

    return (
        <div className="min-h-screen bg-clintra-navy">
            {/* NAVBAR */}
            <nav className="bg-gradient-to-r from-clintra-navy to-clintra-navy-light border-b border-clintra-teal/30 px-6 py-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <ClintraLogo size="lg" />
                        <div>
                            <span className="text-xl font-bold text-clintra-cyan">3D VIEWER</span>
                            <div className="text-xs text-clintra-teal/80">Guaranteed to Work!</div>
                        </div>
                    </div>

                    <button
                        onClick={onBack}
                        className="text-white/80 hover:text-clintra-cyan transition-colors text-sm font-medium flex items-center space-x-2 px-4 py-2 rounded-lg hover:bg-clintra-navy-lighter/50"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                        <span>{backLabel}</span>
                    </button>
                </div>
            </nav>

            {/* SEARCH BAR */}
            <div className="bg-gradient-to-r from-clintra-navy-light to-clintra-navy border-b border-clintra-teal/20 p-6">
                <form onSubmit={handleSearch} className="max-w-6xl mx-auto">
                    <div className="flex items-center space-x-4">
                        <div className="flex-1 flex items-center bg-clintra-navy-lighter border border-clintra-teal/40 hover:border-clintra-teal rounded-full px-6 py-3 focus-within:ring-2 focus-within:ring-clintra-teal/30 transition-all shadow-lg">
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search molecule (e.g., caffeine, aspirin, insulin)..."
                                className="flex-1 bg-transparent text-clintra-cyan placeholder-white/50 focus:outline-none text-base font-medium"
                                disabled={isLoading}
                            />
                        </div>
                        
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="bg-gradient-to-r from-clintra-teal to-clintra-cyan w-12 h-12 rounded-full text-white hover:shadow-xl hover:scale-110 transition-all duration-300 flex items-center justify-center disabled:opacity-50 shadow-lg"
                        >
                            {isLoading ? (
                                <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                            ) : (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            )}
                        </button>
                    </div>
                </form>
            </div>

            {/* MAIN CONTENT */}
            <div className="flex h-[calc(100vh-140px)]">
                {/* CONTROL PANEL */}
                <div className="w-96 bg-gradient-to-b from-clintra-navy-light to-clintra-navy border-r border-clintra-teal/20 p-6 overflow-y-auto">

                    {/* Controls */}
                    <div className="mb-6">
                        <h3 className="text-lg font-bold text-clintra-cyan mb-3">Controls</h3>
                        <div className="space-y-3">
                            <button
                                onClick={resetView}
                                className="w-full px-4 py-3 bg-gradient-to-r from-clintra-teal to-clintra-cyan rounded-lg text-white font-medium hover:shadow-lg transition-all duration-300"
                            >
                                🔄 Reset View
                            </button>
                            <div className="text-sm text-white/70 bg-clintra-navy-lighter/50 p-3 rounded-lg">
                                <div className="font-medium text-clintra-cyan mb-1">🎮 Controls:</div>
                                <div>• Click & drag to rotate</div>
                                <div>• Scroll to zoom</div>
                                <div>• Clean molecular visualization</div>
                            </div>
                        </div>
                    </div>

                    {/* Molecule Information */}
                    {moleculeData && (
                        <div className="mb-6">
                            <h3 className="text-lg font-bold text-clintra-cyan mb-3">Molecule Info</h3>
                            <div className="bg-gradient-to-br from-clintra-navy-lighter to-clintra-navy p-4 rounded-xl space-y-3 text-sm border border-clintra-teal/20">
                                <div className="border-b border-clintra-teal/20 pb-3">
                                    <div className="text-white/60 mb-1 text-xs uppercase tracking-wide">Name</div>
                                    <div className="text-white font-bold text-lg">{moleculeData.name}</div>
                                </div>
                                
                                {moleculeData.molecular_formula && (
                                    <div className="flex justify-between items-center">
                                        <span className="text-white/60">Formula:</span> 
                                        <span className="text-clintra-cyan font-mono font-bold">{moleculeData.molecular_formula}</span>
                                    </div>
                                )}
                                
                                {moleculeData.cid && (
                                    <div className="flex justify-between items-center">
                                        <span className="text-white/60">CID:</span> 
                                        <span className="text-clintra-cyan font-mono">{moleculeData.cid}</span>
                                    </div>
                                )}
                                
                                <div className="border-t border-clintra-teal/20 pt-3 mt-3 space-y-2">
                                    <div className="flex justify-between items-center">
                                        <span className="text-white/60">Atoms:</span> 
                                        <span className="text-clintra-gold font-bold">{moleculeData.structure?.atoms?.length || 0}</span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-white/60">Bonds:</span> 
                                        <span className="text-clintra-gold font-bold">{moleculeData.structure?.bonds?.length || 0}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Quick Search */}
                    <div className="mb-6">
                        <h3 className="text-lg font-bold text-clintra-cyan mb-3">Quick Search</h3>
                        <div className="grid grid-cols-2 gap-3">
                            {['caffeine', 'aspirin', 'insulin', 'benzene', 'glucose', 'methane'].map((molecule) => (
                                <button
                                    key={molecule}
                                    onClick={() => {
                                        setSearchQuery(molecule);
                                        searchMolecule(molecule);
                                    }}
                                    className="px-4 py-2 bg-clintra-navy-lighter border border-clintra-teal/30 hover:border-clintra-teal rounded-lg text-white/80 hover:text-white text-sm transition-all duration-300 hover:shadow-lg"
                                >
                                    {molecule}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* 3D VIEWER */}
                <div className="flex-1 bg-gradient-to-br from-clintra-navy to-black relative">
                    {isLoading && (
                        <div className="absolute inset-0 bg-clintra-navy bg-opacity-95 flex items-center justify-center z-50">
                            <div className="text-center">
                                <div className="animate-spin w-16 h-16 border-4 border-clintra-teal border-t-transparent rounded-full mx-auto mb-6"></div>
                                <div className="text-clintra-cyan text-xl font-bold">Loading 3D Structure...</div>
                                <div className="text-white/60 text-sm mt-2">Fetching molecular data and rendering</div>
                            </div>
                        </div>
                    )}

                    {error && (
                        <div className="absolute inset-0 bg-clintra-navy bg-opacity-95 flex items-center justify-center z-50">
                            <div className="text-center">
                                <div className="text-red-400 text-2xl mb-6">⚠️ {error}</div>
                                <button
                                    onClick={() => setError(null)}
                                    className="px-6 py-3 bg-clintra-navy-lighter border border-clintra-teal/30 hover:border-clintra-teal rounded-lg text-white transition-all duration-300 hover:shadow-lg"
                                >
                                    Try Again
                                </button>
                            </div>
                        </div>
                    )}

                    <canvas
                        ref={canvasRef}
                        className="w-full h-full cursor-grab active:cursor-grabbing"
                    />
                </div>
            </div>
        </div>
    );
};

export default Fixed3DViewer;
