"use client";

import React, { useEffect, useRef } from "react";

export interface BioreactorSceneProps {
  rpm?: number;
  aerationVvm?: number;
  scrollProgress?: number;
  compact?: boolean;
  interactive?: boolean;
  className?: string;
}

interface Bubble {
  x: number;
  y: number;
  z: number;
  radius: number;
  speed: number;
  swirlSpeed: number;
  phase: number;
}

interface PipePulse {
  progress: number;
  speed: number;
}

export function BioreactorScene({
  rpm = 175,
  aerationVvm = 0.65,
  scrollProgress = 0,
  compact = false,
  interactive = true,
  className = "",
}: BioreactorSceneProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const stateRef = useRef({
    yaw: 0.35,
    pitch: 0.15,
    isDragging: false,
    lastMouseX: 0,
    lastMouseY: 0,
    targetYaw: 0.35,
  });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let width = (canvas.width = canvas.parentElement?.clientWidth || 500);
    let height = (canvas.height = canvas.parentElement?.clientHeight || 500);

    const handleResize = () => {
      if (!canvas || !canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.clientWidth;
      height = canvas.height = canvas.parentElement.clientHeight;
    };
    window.addEventListener("resize", handleResize);

    // Initialize bubbles
    const bubbleCount = compact ? 50 : 95;
    const bubbles: Bubble[] = Array.from({ length: bubbleCount }, () => ({
      x: (Math.random() - 0.5) * 60,
      y: 60 + Math.random() * 120, // relative to reactor center
      z: (Math.random() - 0.5) * 60,
      radius: 1.5 + Math.random() * 2.8,
      speed: 0.7 + Math.random() * 1.5,
      swirlSpeed: 0.02 + Math.random() * 0.03,
      phase: Math.random() * Math.PI * 2,
    }));

    // Pipeline pulses
    const pipePulses: PipePulse[] = Array.from({ length: 6 }, (_, i) => ({
      progress: i / 6,
      speed: 0.006 + Math.random() * 0.004,
    }));

    let rotationAngle = 0;
    let waveTime = 0;

    const render = () => {
      animId = requestAnimationFrame(render);

      // Smooth yaw interpolation
      const state = stateRef.current;
      state.yaw += (state.targetYaw + scrollProgress * 1.8 - state.yaw) * 0.06;

      ctx.clearRect(0, 0, width, height);

      const cx = width / 2;
      const cy = height / 2 + 10;
      const scale = compact ? Math.min(width, height) / 400 : Math.min(width, height) / 360;

      // Hydrodynamic rotation speed
      const rotSpeed = (rpm / 60) * 0.08;
      rotationAngle += rotSpeed;
      waveTime += 0.045;

      // 3D Isometric / Perspective projection helper
      const project = (x: number, y: number, z: number) => {
        // Rotate around Y axis (yaw)
        const cosY = Math.cos(state.yaw);
        const sinY = Math.sin(state.yaw);
        const rx = x * cosY - z * sinY;
        const rz = x * sinY + z * cosY;

        // Rotate around X axis (pitch)
        const cosX = Math.cos(state.pitch);
        const sinX = Math.sin(state.pitch);
        const ry = y * cosX - rz * sinX;
        const finalZ = y * sinX + rz * cosX;

        // Perspective
        const fov = 420;
        const pScale = fov / (fov + finalZ);
        return {
          px: cx + rx * scale * pScale,
          py: cy + ry * scale * pScale,
          depth: finalZ,
          scale: pScale,
        };
      };

      // 1. Draw Connecting Fluid Pipes (Behind reactor)
      const drawPipes = () => {
        ctx.save();
        ctx.lineWidth = 4 * scale;
        ctx.strokeStyle = "rgba(34, 211, 238, 0.22)";

        // Left feed line
        ctx.beginPath();
        const p1 = project(-120, -140, -40);
        const p2 = project(-80, -110, -10);
        const p3 = project(-55, -80, 0);
        ctx.moveTo(p1.px, p1.py);
        ctx.bezierCurveTo(p2.px, p2.py, p2.px, p2.py, p3.px, p3.py);
        ctx.stroke();

        // Right harvest line
        ctx.beginPath();
        ctx.strokeStyle = "rgba(16, 185, 129, 0.22)";
        const q1 = project(55, 90, 0);
        const q2 = project(85, 120, -10);
        const q3 = project(120, 140, -40);
        ctx.moveTo(q1.px, q1.py);
        ctx.bezierCurveTo(q2.px, q2.py, q2.px, q2.py, q3.px, q3.py);
        ctx.stroke();

        // Pipe moving pulses
        pipePulses.forEach((pulse) => {
          pulse.progress += pulse.speed;
          if (pulse.progress > 1) pulse.progress = 0;

          // Draw left pulse
          const t = pulse.progress;
          const lx = -120 + t * 65;
          const ly = -140 + t * 60;
          const lp = project(lx, ly, -20);
          ctx.beginPath();
          ctx.arc(lp.px, lp.py, 3.2 * scale, 0, Math.PI * 2);
          ctx.fillStyle = "#22d3ee";
          ctx.shadowColor = "#22d3ee";
          ctx.shadowBlur = 8;
          ctx.fill();

          // Draw right pulse
          const rx = 55 + t * 65;
          const ry = 90 + t * 50;
          const rp = project(rx, ry, -20);
          ctx.beginPath();
          ctx.arc(rp.px, rp.py, 3.2 * scale, 0, Math.PI * 2);
          ctx.fillStyle = "#34d399";
          ctx.shadowColor = "#34d399";
          ctx.shadowBlur = 8;
          ctx.fill();
        });
        ctx.restore();
      };
      drawPipes();

      // 2. Telemetry Orbit Calibration Ring (Holographic Equatorial)
      const drawOrbitRing = () => {
        ctx.save();
        ctx.beginPath();
        const steps = 48;
        for (let i = 0; i <= steps; i++) {
          const theta = (i / steps) * Math.PI * 2;
          const ringR = 88;
          const pt = project(Math.cos(theta) * ringR, 5, Math.sin(theta) * ringR);
          if (i === 0) ctx.moveTo(pt.px, pt.py);
          else ctx.lineTo(pt.px, pt.py);
        }
        ctx.strokeStyle = "rgba(34, 211, 238, 0.28)";
        ctx.lineWidth = 1.2;
        ctx.stroke();

        // Holographic tick marks
        for (let i = 0; i < 12; i++) {
          const theta = (i / 12) * Math.PI * 2;
          const r1 = 86;
          const r2 = 91;
          const pStart = project(Math.cos(theta) * r1, 5, Math.sin(theta) * r1);
          const pEnd = project(Math.cos(theta) * r2, 5, Math.sin(theta) * r2);
          ctx.beginPath();
          ctx.moveTo(pStart.px, pStart.py);
          ctx.lineTo(pEnd.px, pEnd.py);
          ctx.strokeStyle = i % 3 === 0 ? "rgba(52, 211, 153, 0.7)" : "rgba(34, 211, 238, 0.4)";
          ctx.stroke();
        }
        ctx.restore();
      };
      drawOrbitRing();

      // 3. Reactor Vessel Geometry Parameters
      const vesselRadius = 60;
      const vesselTopY = -95;
      const vesselBottomY = 95;
      const liquidLevelY = -35; // liquid height inside reactor

      // 4. Stainless Steel Hemispherical Dished Bottom
      const drawDishedBottom = () => {
        ctx.save();
        const bPt = project(0, vesselBottomY, 0);
        const grad = ctx.createLinearGradient(bPt.px - 60 * scale, bPt.py, bPt.px + 60 * scale, bPt.py);
        grad.addColorStop(0, "#1e293b");
        grad.addColorStop(0.5, "#475569");
        grad.addColorStop(1, "#0f172a");

        ctx.beginPath();
        const left = project(-vesselRadius, vesselBottomY, 0);
        const right = project(vesselRadius, vesselBottomY, 0);
        const bottom = project(0, vesselBottomY + 28, 0);

        ctx.moveTo(left.px, left.py);
        ctx.bezierCurveTo(left.px, bottom.py, right.px, bottom.py, right.px, right.py);
        ctx.fillStyle = grad;
        ctx.fill();
        ctx.strokeStyle = "rgba(148, 163, 184, 0.35)";
        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.restore();
      };
      drawDishedBottom();

      // 5. Internal Liquid Broth Column
      const drawLiquidVolume = () => {
        ctx.save();
        const leftTop = project(-vesselRadius + 2, liquidLevelY, 0);
        const rightTop = project(vesselRadius - 2, liquidLevelY, 0);
        const rightBottom = project(vesselRadius - 2, vesselBottomY, 0);
        const leftBottom = project(-vesselRadius + 2, vesselBottomY, 0);

        // Fluid gradient with bioluminescent depth
        const fluidGrad = ctx.createLinearGradient(leftTop.px, leftTop.py, rightTop.px, rightBottom.py);
        fluidGrad.addColorStop(0, "rgba(8, 70, 95, 0.72)");
        fluidGrad.addColorStop(0.5, "rgba(6, 95, 70, 0.68)");
        fluidGrad.addColorStop(1, "rgba(4, 40, 50, 0.82)");

        ctx.beginPath();
        ctx.moveTo(leftTop.px, leftTop.py);

        // Dynamic surface meniscus wave
        const waveSteps = 24;
        for (let i = 0; i <= waveSteps; i++) {
          const u = i / waveSteps;
          const wx = (-vesselRadius + 2) + u * (vesselRadius * 2 - 4);
          const waveOffset = Math.sin(u * Math.PI * 3 + waveTime) * (1.6 + (rpm / 200) * 2.2);
          const pt = project(wx, liquidLevelY + waveOffset, 0);
          ctx.lineTo(pt.px, pt.py);
        }

        ctx.lineTo(rightBottom.px, rightBottom.py);
        ctx.lineTo(leftBottom.px, leftBottom.py);
        ctx.closePath();
        ctx.fillStyle = fluidGrad;
        ctx.fill();

        // Inner glowing meniscus surface rim
        ctx.beginPath();
        for (let i = 0; i <= 36; i++) {
          const theta = (i / 36) * Math.PI * 2;
          const mx = Math.cos(theta) * (vesselRadius - 3);
          const mz = Math.sin(theta) * (vesselRadius - 3);
          const mPt = project(mx, liquidLevelY, mz);
          if (i === 0) ctx.moveTo(mPt.px, mPt.py);
          else ctx.lineTo(mPt.px, mPt.py);
        }
        ctx.strokeStyle = "rgba(52, 211, 153, 0.55)";
        ctx.lineWidth = 1.8;
        ctx.stroke();

        ctx.restore();
      };
      drawLiquidVolume();

      // 6. Central Impeller Shaft & Turbines (Rotating 3D)
      const drawImpellers = () => {
        ctx.save();
        // Central drive shaft
        const shaftTop = project(0, vesselTopY - 25, 0);
        const shaftBottom = project(0, vesselBottomY + 5, 0);

        ctx.beginPath();
        ctx.moveTo(shaftTop.px, shaftTop.py);
        ctx.lineTo(shaftBottom.px, shaftBottom.py);
        ctx.strokeStyle = "#94a3b8";
        ctx.lineWidth = 3.5 * scale;
        ctx.stroke();

        // Lower Rushton Turbine (6 blades) at y = 60
        const lowerY = 60;
        const rushtonRadius = 28;
        for (let b = 0; b < 6; b++) {
          const bAngle = rotationAngle + (b / 6) * Math.PI * 2;
          const bx = Math.cos(bAngle) * rushtonRadius;
          const bz = Math.sin(bAngle) * rushtonRadius;

          const hub = project(0, lowerY, 0);
          const tip = project(bx, lowerY, bz);

          ctx.beginPath();
          ctx.moveTo(hub.px, hub.py);
          ctx.lineTo(tip.px, tip.py);
          ctx.strokeStyle = "#38bdf8";
          ctx.lineWidth = 3 * scale;
          ctx.stroke();

          // Blade paddle
          const bladeTop = project(bx, lowerY - 6, bz);
          const bladeBottom = project(bx, lowerY + 6, bz);
          ctx.beginPath();
          ctx.moveTo(bladeTop.px, bladeTop.py);
          ctx.lineTo(bladeBottom.px, bladeBottom.py);
          ctx.strokeStyle = "#22d3ee";
          ctx.lineWidth = 4 * scale;
          ctx.stroke();
        }

        // Upper Pitched Blade Turbine (4 blades) at y = 10
        const upperY = 10;
        const pitchedRadius = 32;
        for (let b = 0; b < 4; b++) {
          const bAngle = rotationAngle + (b / 4) * Math.PI * 2;
          const bx = Math.cos(bAngle) * pitchedRadius;
          const bz = Math.sin(bAngle) * pitchedRadius;

          const hub = project(0, upperY, 0);
          const tip = project(bx, upperY, bz);

          ctx.beginPath();
          ctx.moveTo(hub.px, hub.py);
          ctx.lineTo(tip.px, tip.py);
          ctx.strokeStyle = "#34d399";
          ctx.lineWidth = 3 * scale;
          ctx.stroke();
        }
        ctx.restore();
      };
      drawImpellers();

      // 7. Dynamic Rising Aeration Bubbles
      const drawBubbles = () => {
        ctx.save();
        const vvmFactor = aerationVvm / 0.65;

        bubbles.forEach((b) => {
          // Swirl physics around impeller
          b.phase += (rpm / 160) * 0.04;
          const currentRadius = 8 + Math.sin(b.phase) * 36;
          const bx = Math.cos(b.phase + b.swirlSpeed) * currentRadius;
          const bz = Math.sin(b.phase + b.swirlSpeed) * currentRadius;

          // Ascend
          b.y -= b.speed * (0.8 + vvmFactor * 0.9);
          if (b.y < liquidLevelY) {
            // Reset to bottom sparger
            b.y = vesselBottomY - 10 + Math.random() * 10;
            b.phase = Math.random() * Math.PI * 2;
          }

          const bp = project(bx, b.y, bz);
          ctx.beginPath();
          ctx.arc(bp.px, bp.py, b.radius * scale * bp.scale, 0, Math.PI * 2);
          ctx.fillStyle = "rgba(165, 243, 252, 0.75)";
          ctx.fill();
        });
        ctx.restore();
      };
      drawBubbles();

      // 8. Outer Borosilicate Glass Cylinder (Refractions & Specular Lines)
      const drawGlassCylinder = () => {
        ctx.save();
        const leftTop = project(-vesselRadius, vesselTopY, 0);
        const rightTop = project(vesselRadius, vesselTopY, 0);
        const leftBottom = project(-vesselRadius, vesselBottomY, 0);
        const rightBottom = project(vesselRadius, vesselBottomY, 0);

        // Glass boundary
        ctx.beginPath();
        ctx.moveTo(leftTop.px, leftTop.py);
        ctx.lineTo(leftBottom.px, leftBottom.py);
        ctx.strokeStyle = "rgba(148, 163, 184, 0.4)";
        ctx.lineWidth = 2 * scale;
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(rightTop.px, rightTop.py);
        ctx.lineTo(rightBottom.px, rightBottom.py);
        ctx.strokeStyle = "rgba(148, 163, 184, 0.4)";
        ctx.lineWidth = 2 * scale;
        ctx.stroke();

        // Left specular glass highlight reflection
        const specLeftTop = project(-vesselRadius * 0.68, vesselTopY + 10, 0);
        const specLeftBottom = project(-vesselRadius * 0.68, vesselBottomY - 10, 0);
        ctx.beginPath();
        ctx.moveTo(specLeftTop.px, specLeftTop.py);
        ctx.lineTo(specLeftBottom.px, specLeftBottom.py);
        ctx.strokeStyle = "rgba(255, 255, 255, 0.22)";
        ctx.lineWidth = 4 * scale;
        ctx.stroke();

        // Soft glass shading across face
        const glassGrad = ctx.createLinearGradient(leftTop.px, 0, rightTop.px, 0);
        glassGrad.addColorStop(0, "rgba(255, 255, 255, 0.12)");
        glassGrad.addColorStop(0.15, "rgba(34, 211, 238, 0.05)");
        glassGrad.addColorStop(0.5, "rgba(255, 255, 255, 0.01)");
        glassGrad.addColorStop(0.85, "rgba(16, 185, 129, 0.04)");
        glassGrad.addColorStop(1, "rgba(255, 255, 255, 0.1)");

        ctx.fillStyle = glassGrad;
        ctx.fillRect(leftTop.px, leftTop.py, rightTop.px - leftTop.px, rightBottom.py - rightTop.py);

        ctx.restore();
      };
      drawGlassCylinder();

      // 9. Top Stainless Steel Headplate & Ports
      const drawHeadplate = () => {
        ctx.save();
        const topCenter = project(0, vesselTopY, 0);
        const hpGrad = ctx.createLinearGradient(topCenter.px - 65 * scale, topCenter.py, topCenter.px + 65 * scale, topCenter.py);
        hpGrad.addColorStop(0, "#0f172a");
        hpGrad.addColorStop(0.5, "#475569");
        hpGrad.addColorStop(1, "#1e293b");

        // Flange ring
        ctx.beginPath();
        for (let i = 0; i <= 36; i++) {
          const theta = (i / 36) * Math.PI * 2;
          const hx = Math.cos(theta) * (vesselRadius + 4);
          const hz = Math.sin(theta) * (vesselRadius + 4);
          const pt = project(hx, vesselTopY, hz);
          if (i === 0) ctx.moveTo(pt.px, pt.py);
          else ctx.lineTo(pt.px, pt.py);
        }
        ctx.fillStyle = hpGrad;
        ctx.fill();
        ctx.strokeStyle = "rgba(203, 213, 225, 0.45)";
        ctx.lineWidth = 2.5 * scale;
        ctx.stroke();

        // Top Drive Motor Assembly
        const motorBase = project(0, vesselTopY - 12, 0);
        const motorTop = project(0, vesselTopY - 42, 0);
        ctx.beginPath();
        ctx.moveTo(motorBase.px, motorBase.py);
        ctx.lineTo(motorTop.px, motorTop.py);
        ctx.strokeStyle = "#334155";
        ctx.lineWidth = 18 * scale;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(motorTop.px, motorTop.py, 10 * scale, 0, Math.PI * 2);
        ctx.fillStyle = "#0284c7";
        ctx.shadowColor = "#0284c7";
        ctx.shadowBlur = 10;
        ctx.fill();

        // Probe Entry Port (pH / DO sensor)
        const probePt = project(-28, vesselTopY - 18, 10);
        ctx.beginPath();
        ctx.arc(probePt.px, probePt.py, 3.5 * scale, 0, Math.PI * 2);
        ctx.fillStyle = "#10b981";
        ctx.fill();

        ctx.restore();
      };
      drawHeadplate();
    };

    render();

    // Mouse / Touch Drag Interactivity
    const onMouseDown = (e: MouseEvent) => {
      if (!interactive) return;
      stateRef.current.isDragging = true;
      stateRef.current.lastMouseX = e.clientX;
      stateRef.current.lastMouseY = e.clientY;
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!interactive || !stateRef.current.isDragging) return;
      const dx = e.clientX - stateRef.current.lastMouseX;
      const dy = e.clientY - stateRef.current.lastMouseY;
      stateRef.current.targetYaw += dx * 0.008;
      stateRef.current.pitch = Math.max(-0.25, Math.min(0.45, stateRef.current.pitch + dy * 0.004));
      stateRef.current.lastMouseX = e.clientX;
      stateRef.current.lastMouseY = e.clientY;
    };

    const onMouseUp = () => {
      stateRef.current.isDragging = false;
    };

    const canvasEl = canvas;
    canvasEl.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", handleResize);
      canvasEl.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [rpm, aerationVvm, scrollProgress, compact, interactive]);

  return (
    <div
      className={`relative w-full h-full select-none ${
        interactive ? "cursor-grab active:cursor-grabbing" : ""
      } ${className}`}
      aria-label="Interactive 3D Bioreactor Digital Twin"
    >
      <canvas ref={canvasRef} className="w-full h-full block" />
    </div>
  );
}

export default BioreactorScene;
