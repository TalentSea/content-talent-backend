import React, { useState, useEffect, useRef, useCallback } from 'react';

interface ColorPickerProps {
  color: string;
  onChange: (color: string) => void;
  className?: string;
}

// Convert HEX to HSV
const hexToHsv = (hex: string) => {
  let r = 0, g = 0, b = 0;
  if (hex.length === 4) {
    r = parseInt(hex[1] + hex[1], 16);
    g = parseInt(hex[2] + hex[2], 16);
    b = parseInt(hex[3] + hex[3], 16);
  } else if (hex.length === 7) {
    r = parseInt(hex.substring(1, 3), 16);
    g = parseInt(hex.substring(3, 5), 16);
    b = parseInt(hex.substring(5, 7), 16);
  }
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h = 0, s = 0, v = max;
  const d = max - min;
  s = max === 0 ? 0 : d / max;
  if (max === min) {
    h = 0; // achromatic
  } else {
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }
    h /= 6;
  }
  return { h: h * 360, s: s * 100, v: v * 100 };
};

// Convert HSV to HEX
const hsvToHex = (h: number, s: number, v: number) => {
  h /= 360; s /= 100; v /= 100;
  let r = 0, g = 0, b = 0;
  const i = Math.floor(h * 6);
  const f = h * 6 - i;
  const p = v * (1 - s);
  const q = v * (1 - f * s);
  const t = v * (1 - (1 - f) * s);
  switch (i % 6) {
    case 0: r = v; g = t; b = p; break;
    case 1: r = q; g = v; b = p; break;
    case 2: r = p; g = v; b = t; break;
    case 3: r = p; g = q; b = v; break;
    case 4: r = t; g = p; b = v; break;
    case 5: r = v; g = p; b = q; break;
  }
  const toHex = (x: number) => {
    const hex = Math.round(x * 255).toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  };
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`.toUpperCase();
};

export const ColorPicker: React.FC<ColorPickerProps> = ({ color, onChange, className = '' }) => {
  const [hsv, setHsv] = useState(hexToHsv(color || '#000000'));
  const saturationRef = useRef<HTMLDivElement>(null);
  const hueRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setHsv(hexToHsv(color || '#000000'));
  }, [color]);

  const handleSaturationDrag = useCallback((e: MouseEvent | React.MouseEvent | TouchEvent | React.TouchEvent) => {
    if (!saturationRef.current) return;
    const { left, top, width, height } = saturationRef.current.getBoundingClientRect();
    
    let clientX, clientY;
    if ('touches' in e) {
      clientX = e.touches[0].clientX;
      clientY = e.touches[0].clientY;
    } else {
      clientX = (e as MouseEvent).clientX;
      clientY = (e as MouseEvent).clientY;
    }

    let x = Math.max(0, Math.min(1, (clientX - left) / width));
    let y = Math.max(0, Math.min(1, (clientY - top) / height));

    const s = x * 100;
    const v = (1 - y) * 100;
    
    setHsv(prev => {
      const newHsv = { ...prev, s, v };
      onChange(hsvToHex(newHsv.h, newHsv.s, newHsv.v));
      return newHsv;
    });
  }, [onChange]);

  const handleHueDrag = useCallback((e: MouseEvent | React.MouseEvent | TouchEvent | React.TouchEvent) => {
    if (!hueRef.current) return;
    const { left, width } = hueRef.current.getBoundingClientRect();
    
    let clientX;
    if ('touches' in e) {
      clientX = e.touches[0].clientX;
    } else {
      clientX = (e as MouseEvent).clientX;
    }

    let x = Math.max(0, Math.min(1, (clientX - left) / width));
    const h = x * 360;

    setHsv(prev => {
      const newHsv = { ...prev, h };
      onChange(hsvToHex(newHsv.h, newHsv.s, newHsv.v));
      return newHsv;
    });
  }, [onChange]);

  const onSaturationMouseDown = (e: React.MouseEvent | React.TouchEvent) => {
    handleSaturationDrag(e);
    
    const onMouseMove = (e: MouseEvent | TouchEvent) => handleSaturationDrag(e);
    const onMouseUp = () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('touchmove', onMouseMove);
      window.removeEventListener('touchend', onMouseUp);
    };
    
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    window.addEventListener('touchmove', onMouseMove, { passive: false });
    window.addEventListener('touchend', onMouseUp);
  };

  const onHueMouseDown = (e: React.MouseEvent | React.TouchEvent) => {
    handleHueDrag(e);
    
    const onMouseMove = (e: MouseEvent | TouchEvent) => handleHueDrag(e);
    const onMouseUp = () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('touchmove', onMouseMove);
      window.removeEventListener('touchend', onMouseUp);
    };
    
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    window.addEventListener('touchmove', onMouseMove, { passive: false });
    window.addEventListener('touchend', onMouseUp);
  };

  return (
    <div className={`flex flex-col gap-3 w-56 bg-slate-900 p-3 rounded-xl shadow-xl border border-slate-800 ${className}`}>
      <div 
        ref={saturationRef}
        className="w-full h-40 rounded-lg relative overflow-hidden cursor-crosshair select-none touch-none shadow-inner"
        style={{ backgroundColor: `hsl(${hsv.h}, 100%, 50%)` }}
        onMouseDown={onSaturationMouseDown}
        onTouchStart={onSaturationMouseDown}
      >
        <div className="absolute inset-0" style={{ background: 'linear-gradient(to right, #fff, rgba(255,255,255,0))' }} />
        <div className="absolute inset-0" style={{ background: 'linear-gradient(to top, #000, rgba(0,0,0,0))' }} />
        <div 
          className="absolute w-4 h-4 -ml-2 -mt-2 border-2 border-white rounded-full shadow-md pointer-events-none"
          style={{ 
            left: `${hsv.s}%`, 
            top: `${100 - hsv.v}%`,
            backgroundColor: hsvToHex(hsv.h, hsv.s, hsv.v)
          }}
        />
      </div>

      <div className="space-y-2">
        <div 
          ref={hueRef}
          className="w-full h-3 rounded-full relative cursor-ew-resize select-none touch-none shadow-inner"
          style={{ 
            background: 'linear-gradient(to right, #f00 0%, #ff0 17%, #0f0 33%, #0ff 50%, #00f 67%, #f0f 83%, #f00 100%)'
          }}
          onMouseDown={onHueMouseDown}
          onTouchStart={onHueMouseDown}
        >
          <div 
            className="absolute w-4 h-4 -ml-2 -mt-0.5 bg-white border border-slate-300 rounded-full shadow-md pointer-events-none"
            style={{ left: `${(hsv.h / 360) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
};
