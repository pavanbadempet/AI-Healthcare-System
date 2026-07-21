import React, { useState, useRef, useEffect, MouseEvent as ReactMouseEvent } from 'react';
import { ZoomIn, Sun, Contrast, RotateCcw, Download, Crosshair, ArrowUpDown, Layers } from 'lucide-react';
import { useMaterialRipple } from '@/lib/ripple';
import { DicomMprRendererModal } from '@/components/modals/DicomMprRendererModal';

interface PacsViewerProps {
  mrn: string;
  patientName: string;
  dob: string;
  sex: string;
  imageUrl?: string;
}

type ToolMode = 'pan' | 'zoom' | 'windowLevel' | 'scroll';

export default function PacsViewer({
  mrn,
  patientName,
  dob,
  sex,
  imageUrl = '/pacs_scan_mockup.png'
}: PacsViewerProps) {
  const { triggerRipple } = useMaterialRipple();
  
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);

  // Viewport state
  const [scale, setScale] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [windowCenter, setWindowCenter] = useState(128); // Brightness
  const [windowWidth, setWindowWidth] = useState(256); // Contrast
  const [inverted, setInverted] = useState(false);
  const [sliceIndex, setSliceIndex] = useState(42);
  const [showMprModal, setShowMprModal] = useState(false);
  const maxSlices = 120;

  // Interaction state
  const [activeTool, setActiveTool] = useState<ToolMode>('windowLevel');
  const [isDragging, setIsDragging] = useState(false);
  const [lastMousePos, setLastMousePos] = useState({ x: 0, y: 0 });

  // Load image
  useEffect(() => {
    const img = new Image();
    img.src = imageUrl;
    img.onload = () => {
      imageRef.current = img;
      resetViewport();
    };
  }, [imageUrl]);

  // Render loop
  useEffect(() => {
    renderCanvas();
  }, [scale, pan, windowCenter, windowWidth, inverted, sliceIndex]);

  const resetViewport = () => {
    if (!imageRef.current || !canvasRef.current || !containerRef.current) return;
    
    const container = containerRef.current;
    const img = imageRef.current;
    
    // Fit to container
    const scaleX = container.clientWidth / img.width;
    const scaleY = container.clientHeight / img.height;
    const initialScale = Math.min(scaleX, scaleY) * 0.95; // 95% fit
    
    setScale(initialScale);
    setPan({ 
      x: (container.clientWidth - img.width * initialScale) / 2, 
      y: (container.clientHeight - img.height * initialScale) / 2 
    });
    setWindowCenter(128);
    setWindowWidth(256);
    setInverted(false);
  };

  const renderCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d', { willReadFrequently: true });
    const img = imageRef.current;
    const container = containerRef.current;

    if (!canvas || !ctx || !img || !container) return;

    // Set canvas resolution to match container size
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;

    // Clear background
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Apply transforms
    ctx.save();
    ctx.translate(pan.x, pan.y);
    ctx.scale(scale, scale);

    // Draw base image
    ctx.drawImage(img, 0, 0);
    
    // Apply Window/Level (Brightness/Contrast) filter using pixel manipulation
    if (windowCenter !== 128 || windowWidth !== 256 || inverted) {
      // Get the bounding box of the drawn image within the canvas to avoid processing empty black space
      const drawX = Math.max(0, -pan.x / scale);
      const drawY = Math.max(0, -pan.y / scale);
      const drawW = Math.min(img.width, canvas.width / scale);
      const drawH = Math.min(img.height, canvas.height / scale);
      
      const realX = pan.x + drawX * scale;
      const realY = pan.y + drawY * scale;
      const realW = drawW * scale;
      const realH = drawH * scale;

      // Only process if visible
      if (realW > 0 && realH > 0 && realX < canvas.width && realY < canvas.height) {
        const imageData = ctx.getImageData(realX, realY, realW, realH);
        const data = imageData.data;

        // WL Math
        const minIntensity = windowCenter - 0.5 - (windowWidth - 1) / 2;
        const maxIntensity = windowCenter - 0.5 + (windowWidth - 1) / 2;
        const slope = 255 / windowWidth;

        for (let i = 0; i < data.length; i += 4) {
          // Grayscale assumption: use R channel for intensity
          let intensity = data[i];
          
          if (intensity <= minIntensity) {
            intensity = 0;
          } else if (intensity > maxIntensity) {
            intensity = 255;
          } else {
            intensity = (intensity - minIntensity) * slope;
          }

          if (inverted) {
            intensity = 255 - intensity;
          }

          data[i] = intensity;
          data[i+1] = intensity;
          data[i+2] = intensity;
        }
        ctx.putImageData(imageData, realX, realY);
      }
    }

    ctx.restore();
  };

  const handleMouseDown = (e: ReactMouseEvent) => {
    setIsDragging(true);
    setLastMousePos({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e: ReactMouseEvent) => {
    if (!isDragging) return;

    const dx = e.clientX - lastMousePos.x;
    const dy = e.clientY - lastMousePos.y;

    if (activeTool === 'pan') {
      setPan(prev => ({ x: prev.x + dx, y: prev.y + dy }));
    } else if (activeTool === 'windowLevel') {
      setWindowWidth(prev => Math.max(1, prev + dx * 2));
      setWindowCenter(prev => Math.max(0, Math.min(255, prev - dy * 2)));
    } else if (activeTool === 'zoom') {
      setScale(prev => Math.max(0.1, prev * (1 - dy * 0.01)));
    } else if (activeTool === 'scroll') {
      setSliceIndex(prev => {
        const next = prev - Math.sign(dy);
        return Math.max(1, Math.min(maxSlices, next));
      });
    }

    setLastMousePos({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
    
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      
      setScale(prev => prev * zoomFactor);
      setPan(prev => ({
        x: mouseX - (mouseX - prev.x) * zoomFactor,
        y: mouseY - (mouseY - prev.y) * zoomFactor
      }));
    }
  };

  return (
    <div className="flex flex-col h-full bg-black rounded-lg overflow-hidden border border-zinc-800 shadow-xl font-mono select-none">
      
      {/* Top Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-zinc-950 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <button 
            className={`p-2 rounded hover:bg-zinc-800 transition-colors ${activeTool === 'windowLevel' ? 'bg-indigo-900/50 text-indigo-400' : 'text-zinc-400'}`}
            onClick={(e) => { triggerRipple(e); setActiveTool('windowLevel'); }}
            title="Window/Level (Contrast/Brightness)"
          >
            <Sun size={18} />
          </button>
          <button 
            className={`p-2 rounded hover:bg-zinc-800 transition-colors ${activeTool === 'pan' ? 'bg-indigo-900/50 text-indigo-400' : 'text-zinc-400'}`}
            onClick={(e) => { triggerRipple(e); setActiveTool('pan'); }}
            title="Pan"
          >
            <Crosshair size={18} />
          </button>
          <button 
            className={`p-2 rounded hover:bg-zinc-800 transition-colors ${activeTool === 'zoom' ? 'bg-indigo-900/50 text-indigo-400' : 'text-zinc-400'}`}
            onClick={(e) => { triggerRipple(e); setActiveTool('zoom'); }}
            title="Zoom"
          >
            <ZoomIn size={18} />
          </button>
          <button 
            className={`p-2 rounded hover:bg-zinc-800 transition-colors ${activeTool === 'scroll' ? 'bg-indigo-900/50 text-indigo-400' : 'text-zinc-400'}`}
            onClick={(e) => { triggerRipple(e); setActiveTool('scroll'); }}
            title="Scroll Slices"
          >
            <ArrowUpDown size={18} />
          </button>
          
          <div className="w-px h-6 bg-zinc-800 mx-2" />
          
          <button 
            className={`p-2 rounded hover:bg-zinc-800 transition-colors ${inverted ? 'bg-indigo-900/50 text-indigo-400' : 'text-zinc-400'}`}
            onClick={(e) => { triggerRipple(e); setInverted(!inverted); }}
            title="Invert Colors"
          >
            <Contrast size={18} />
          </button>
          <button 
            className="p-2 rounded text-zinc-400 hover:bg-zinc-800 transition-colors"
            onClick={(e) => { triggerRipple(e); resetViewport(); }}
            title="Reset Viewport"
          >
            <RotateCcw size={18} />
          </button>
        </div>
        
        <div className="flex items-center gap-2">
           <button
             className="p-2 rounded text-purple-400 hover:bg-zinc-800 transition-colors flex items-center gap-1 text-xs font-mono font-bold"
             onClick={(e) => { triggerRipple(e); setShowMprModal(true); }}
             title="Open 3D Multi-Planar Reconstruction"
           >
             <Layers size={18} />
             <span>3D MPR</span>
           </button>
           <button className="p-2 rounded text-zinc-400 hover:bg-zinc-800 transition-colors" title="Download DICOM">
             <Download size={18} />
           </button>
        </div>
      </div>

      {/* Main Viewport */}
      <div 
        ref={containerRef}
        className="relative flex-1 min-h-[400px] bg-black overflow-hidden cursor-crosshair"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        <canvas 
          ref={canvasRef}
          className="absolute inset-0 w-full h-full"
        />

        {/* Clinical Overlays */}
        <div className="absolute top-4 left-4 text-[11px] text-amber-400/80 pointer-events-none drop-shadow-md">
          <div>{patientName.toUpperCase()}</div>
          <div>{mrn}</div>
          <div>DOB: {dob} | SEX: {sex}</div>
        </div>
        
        <div className="absolute top-4 right-4 text-[11px] text-amber-400/80 text-right pointer-events-none drop-shadow-md">
          <div>HOSPITAL_SYS_AI</div>
          <div>CT ABDOMEN W/O CONTRAST</div>
          <div>SERIES: 2</div>
        </div>

        <div className="absolute bottom-4 left-4 text-[11px] text-amber-400/80 pointer-events-none drop-shadow-md">
          <div>Z: {(scale * 100).toFixed(0)}%</div>
          <div>W: {windowWidth.toFixed(0)} L: {windowCenter.toFixed(0)}</div>
        </div>

        <div className="absolute bottom-4 right-4 text-[11px] text-amber-400/80 text-right pointer-events-none drop-shadow-md">
          <div>THK: 1.25mm</div>
          <div>Im: {sliceIndex}/{maxSlices}</div>
        </div>
        
        {/* Slice Scrollbar Indicator */}
        <div className="absolute right-1 top-1/4 bottom-1/4 w-1 bg-zinc-900/50 rounded pointer-events-none">
           <div 
             className="w-full bg-amber-500/50 rounded" 
             style={{ 
               height: `${100 / maxSlices}%`, 
               transform: `translateY(${(sliceIndex / maxSlices) * 100 * (maxSlices-1)}%)`
             }} 
           />
        </div>
      </div>

      {showMprModal && (
        <DicomMprRendererModal
          patientName={patientName}
          mrn={mrn}
          onClose={() => setShowMprModal(false)}
        />
      )}
    </div>
  );
}
